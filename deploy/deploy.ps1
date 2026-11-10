param(
    [string]$Region = "ap-south-1",
    [string]$Profile = "default",
    [string]$SubnetId = "subnet-0d9b567a0c747c974",
    [string]$InstanceType = "t3.medium"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$accountId = (& aws sts get-caller-identity --profile $Profile --region $Region --query Account --output text).Trim()
if ($LASTEXITCODE -ne 0) { throw "Unable to identify the AWS account." }

$bucket = "codeautopsy-$accountId-$Region-artifacts"
$artifactKey = "deploy/source.zip"
$archive = Join-Path $env:TEMP "codeautopsy-deploy-$([guid]::NewGuid().ToString('N')).zip"

try {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & aws s3api head-bucket --bucket $bucket --profile $Profile --region $Region 2>$null
    $headBucketExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    if ($headBucketExitCode -ne 0) {
        & aws s3api create-bucket --bucket $bucket --create-bucket-configuration "LocationConstraint=$Region" --profile $Profile --region $Region
        if ($LASTEXITCODE -ne 0) { throw "Could not create the private deployment bucket." }
    }

    & aws s3api put-public-access-block --bucket $bucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" --profile $Profile --region $Region
    if ($LASTEXITCODE -ne 0) { throw "Could not block public access to the deployment bucket." }
    & aws s3api put-bucket-encryption --bucket $bucket --server-side-encryption-configuration "Rules=[{ApplyServerSideEncryptionByDefault={SSEAlgorithm=AES256}}]" --profile $Profile --region $Region
    if ($LASTEXITCODE -ne 0) { throw "Could not enable encryption on the deployment bucket." }
    & aws s3api put-bucket-versioning --bucket $bucket --versioning-configuration Status=Enabled --profile $Profile --region $Region
    if ($LASTEXITCODE -ne 0) { throw "Could not enable deployment artifact versioning." }

    @'
import os
import sys
import zipfile

root, archive = sys.argv[1:]
excluded_dirs = {
    ".git", "node_modules", "dist", "coverage", ".venv", "venv",
    "__pycache__", ".pytest_cache", ".mypy_cache", "uploads", "temp", "logs",
}
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in excluded_dirs]
        for name in files:
            if name == ".env" or name.startswith(".env.") or name.endswith((".pyc", ".pyo", ".db", ".sqlite")):
                continue
            path = os.path.join(current, name)
            relative = os.path.relpath(path, root)
            output.write(path, relative)
'@ | python - $root $archive
    if ($LASTEXITCODE -ne 0) { throw "Could not prepare the deployment archive." }

    & aws s3 cp $archive "s3://$bucket/$artifactKey" --sse AES256 --profile $Profile --region $Region
    if ($LASTEXITCODE -ne 0) { throw "Could not upload the deployment archive." }

    $amiId = (& aws ec2 describe-images --owners amazon --filters "Name=name,Values=al2023-ami-2023.*-kernel-6.1-x86_64" "Name=state,Values=available" --query "sort_by(Images,&CreationDate)[-1].ImageId" --output text --profile $Profile --region $Region).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $amiId -or $amiId -eq "None") { throw "Could not find an available Amazon Linux 2023 AMI." }

    $vpcId = (& aws ec2 describe-subnets --subnet-ids $SubnetId --query "Subnets[0].VpcId" --output text --profile $Profile --region $Region).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $vpcId -or $vpcId -eq "None") { throw "Could not find the VPC for the selected subnet." }

    $prefixListId = (& aws ec2 describe-managed-prefix-lists --filters "Name=prefix-list-name,Values=com.amazonaws.global.cloudfront.origin-facing" --query "PrefixLists[0].PrefixListId" --output text --profile $Profile --region $Region).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $prefixListId -or $prefixListId -eq "None") { throw "Could not find the CloudFront origin prefix list." }

    & aws cloudformation deploy `
        --template-file (Join-Path $PSScriptRoot "cloudformation.yml") `
        --stack-name codeautopsy `
        --capabilities CAPABILITY_IAM `
        --no-fail-on-empty-changeset `
        --parameter-overrides "VpcId=$vpcId" "SubnetId=$SubnetId" "AmiId=$amiId" "InstanceType=$InstanceType" "ArtifactBucket=$bucket" "ArtifactKey=$artifactKey" "CloudFrontOriginPrefixListId=$prefixListId" `
        --profile $Profile `
        --region $Region
    if ($LASTEXITCODE -ne 0) { throw "CloudFormation deployment failed. Inspect the codeautopsy stack events before retrying." }

    & aws cloudformation describe-stacks --stack-name codeautopsy --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table --profile $Profile --region $Region
    if ($LASTEXITCODE -ne 0) { throw "Could not retrieve deployment outputs." }
}
finally {
    if (Test-Path -LiteralPath $archive) {
        Remove-Item -LiteralPath $archive -Force
    }
}
