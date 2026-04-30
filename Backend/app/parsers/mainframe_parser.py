"""
Mainframe Parser

Parser for mainframe-related files including JCL (Job Control Language).
"""

import logging
import re

from app.parsers.base_parser import (
    BaseParser, ParseResult, CodeNode, NodeType
)

logger = logging.getLogger(__name__)


class MainframeParser(BaseParser):
    """Parser for mainframe files (JCL, etc.)."""
    
    def __init__(self):
        super().__init__()
        self.language = "mainframe"
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a mainframe file."""
        lower_path = file_path.lower()
        return (
            lower_path.endswith('.jcl') or
            lower_path.endswith('.jcl') or
            lower_path.endswith('.proc') or
            'jcl' in lower_path
        )
    
    def parse(self, file_path: str, content: str) -> ParseResult:
        """
        Parse mainframe JCL code.
        
        Args:
            file_path: Path to JCL file
            content: JCL source code
            
        Returns:
            ParseResult with extracted structure
        """
        result = ParseResult(
            file_path=file_path,
            language=self.language,
            success=False
        )
        
        try:
            # Count lines
            code_lines, comment_lines, blank_lines = self._count_lines(content)
            result.lines_of_code = code_lines
            result.comment_lines = comment_lines
            result.blank_lines = blank_lines
            
            # Parse JCL structure
            self._parse_jobs(content, result)
            self._parse_steps(content, result)
            self._parse_dd_statements(content, result)
            self._parse_procs(content, result)
            
            # Calculate complexity
            result.complexity_score = self._calculate_complexity(result.nodes)
            
            result.success = True
            logger.info(f"Successfully parsed JCL file {file_path}: {len(result.nodes)} nodes")
            
        except Exception as e:
            logger.error(f"Failed to parse JCL file {file_path}: {e}")
            result.errors.append(str(e))
            result.success = False
        
        return result
    
    def _parse_jobs(self, content: str, result: ParseResult) -> None:
        """Parse JCL job statements."""
        # JCL job statements start with //jobname JOB
        job_pattern = re.compile(
            r'^//(\w+)\s+JOB\s+',
            re.MULTILINE | re.IGNORECASE
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = job_pattern.search(line)
            if match:
                job_name = match.group(1)
                node = CodeNode(
                    node_type=NodeType.JOB,
                    name=job_name,
                    line_start=i,
                    line_end=i
                )
                result.nodes.append(node)
                result.metadata.setdefault('jobs', []).append(job_name)
                logger.debug(f"Found JCL job: {job_name}")
    
    def _parse_steps(self, content: str, result: ParseResult) -> None:
        """Parse JCL step statements."""
        # JCL steps start with //stepname EXEC
        step_pattern = re.compile(
            r'^//(\w+)\s+EXEC\s+',
            re.MULTILINE | re.IGNORECASE
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = step_pattern.search(line)
            if match:
                step_name = match.group(1)
                node = CodeNode(
                    node_type=NodeType.STEP,
                    name=step_name,
                    line_start=i,
                    line_end=i
                )
                result.nodes.append(node)
                result.metadata.setdefault('steps', []).append(step_name)
                
                # Extract program name if present
                prog_match = re.search(r'PGM=(\w+)', line, re.IGNORECASE)
                if prog_match:
                    program = prog_match.group(1)
                    node.metadata['program'] = program
                    result.dependencies.append(program)
                
                # Extract procedure name if present
                proc_match = re.search(r'PROC=(\w+)', line, re.IGNORECASE)
                if proc_match:
                    procedure = proc_match.group(1)
                    node.metadata['procedure'] = procedure
                    result.dependencies.append(procedure)
    
    def _parse_dd_statements(self, content: str, result: ParseResult) -> None:
        """Parse JCL DD (Data Definition) statements."""
        # DD statements define datasets
        dd_pattern = re.compile(
            r'^//(\w+)\s+DD\s+',
            re.MULTILINE | re.IGNORECASE
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = dd_pattern.search(line)
            if match:
                dd_name = match.group(1)
                node = CodeNode(
                    node_type=NodeType.DD_STATEMENT,
                    name=dd_name,
                    line_start=i,
                    line_end=i
                )
                
                # Extract dataset name if present
                dsn_match = re.search(r'DSN=([^\s,]+)', line, re.IGNORECASE)
                if dsn_match:
                    dataset = dsn_match.group(1)
                    node.metadata['dataset'] = dataset
                    result.metadata.setdefault('datasets', []).append(dataset)
                
                result.nodes.append(node)
    
    def _parse_procs(self, content: str, result: ParseResult) -> None:
        """Parse JCL procedure definitions."""
        # Procedures start with //procname PROC
        proc_pattern = re.compile(
            r'^//(\w+)\s+PROC\s+',
            re.MULTILINE | re.IGNORECASE
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            match = proc_pattern.search(line)
            if match:
                proc_name = match.group(1)
                node = CodeNode(
                    node_type=NodeType.PROCEDURE,
                    name=proc_name,
                    line_start=i,
                    line_end=i
                )
                result.nodes.append(node)
                result.metadata.setdefault('procedures', []).append(proc_name)
    
    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a JCL comment."""
        # JCL comments start with //*
        stripped = line.strip()
        return stripped.startswith('//*')

# Made with Bob
