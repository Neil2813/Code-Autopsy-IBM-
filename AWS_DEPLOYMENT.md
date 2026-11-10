# AWS Deployment

The included deployment provides one working AWS-hosted application without requiring a local Docker daemon. It uses:

- **Amazon EC2** to run the frontend, FastAPI backend, PostgreSQL, and Redis with Docker Compose.
- **Amazon CloudFront** to provide HTTPS and restrict direct access to the EC2 HTTP origin.
- **Encrypted EBS storage** for the database, Redis data, and uploaded files.
- **Amazon S3** for encrypted, versioned database and upload backups, retained for 30 days.
- **AWS Systems Manager Session Manager** for instance administration; no inbound SSH port is opened.
- **AWS Secrets Manager** for optional LLM provider credentials.

The instance automatically recovers from EC2 host system-check failures. Docker containers restart after process or instance restarts, while EBS keeps application data persistent.

## Deploy

Requirements: AWS CLI v2 configured with an authorized profile, PowerShell, Python, and an AWS account with permissions to create CloudFormation, IAM, EC2, S3, and CloudFront resources.

From the repository root, run:

```powershell
.\deploy\deploy.ps1
```

By default this uses the `default` AWS CLI profile, the `ap-south-1` region, and a `t3.medium` instance. Override these when needed:

```powershell
.\deploy\deploy.ps1 -Profile my-profile -Region ap-south-1 -InstanceType t3.large
```

The script packages the current source, excludes `.env` files, Git metadata, virtual environments, dependency folders, and local data, uploads the encrypted archive to a private S3 bucket, and deploys `deploy/cloudformation.yml`. It prints the HTTPS CloudFront URL and instance ID when CloudFormation finishes. The initial Docker builds can take several minutes after the stack is created; wait for the app health check before using the URL.

The backend and database are not exposed directly to the internet. CloudFront is the only allowed inbound origin, and the origin is configured for HTTPS-only viewers.

## Configure watsonx.ai credentials

For AI analysis, create an AWS Secrets Manager secret named `codeautopsy/llm` with a JSON object containing the provider credentials:

```json
{
  "WATSONX_API_KEY": "your-watsonx-api-key",
  "WATSONX_PROJECT_ID": "your-watsonx-project-id",
  "WATSONX_URL": "https://us-south.ml.cloud.ibm.com",
  "WATSONX_MODEL": "ibm/granite-13b-chat-v2",
  "PRIMARY_LLM_PROVIDER": "watsonx"
}
```

Do not put credentials in the repository or deployment archive. The instance role can read only this named secret. After creating or rotating it, connect to the instance using Session Manager and run:

```bash
sudo /opt/codeautopsy/deploy/refresh-llm-secret.sh
```

If no secret exists, the app starts with its configured fallback provider. The secret refresh script recreates only the backend container and does not change the database password or stored data.

## Backups and operations

- Database and uploaded-file backups are sent to the private S3 backup bucket daily at 02:30 UTC.
- Backups expire after 30 days; noncurrent object versions expire after 7 days.
- The database, Redis, and uploaded files persist on encrypted EBS/Docker volumes.
- Use Session Manager for administration. Check `docker-compose -f /opt/codeautopsy/docker-compose.production.yml ps` and `/var/log/codeautopsy-bootstrap.log` for deployment status.
- CloudFront may take several minutes to finish deploying. The application can take additional time to build its containers on first boot.

## Availability and cost

This is a cost-conscious single-instance deployment, not a multi-AZ high-availability architecture. EC2 host recovery and daily off-instance backups reduce recovery risk, but an instance or availability-zone outage can make the app unavailable until recovery. The single `t3.medium` instance, 50 GB encrypted EBS volume, public IPv4 address, CloudFront requests, S3 storage, and data transfer incur charges. A low-traffic deployment is roughly **$40–$60 USD/month** as a planning estimate; actual `ap-south-1` pricing and traffic vary. Use the AWS Pricing Calculator for an estimate before scaling.

For production workloads that require minimal downtime or independent worker scaling, move PostgreSQL to RDS, Redis to ElastiCache, and run the API and worker on multiple ECS tasks behind a load balancer. This costs more and requires adapting the current synchronous analysis flow.
