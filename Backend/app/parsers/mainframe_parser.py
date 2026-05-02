"""
Mainframe Parser

Parser for mainframe-related files including JCL (Job Control Language).
"""

import logging
import re
from typing import Optional, List, Dict

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
        """Parse JCL job statements with enhanced details."""
        # JCL job statements start with //jobname JOB
        job_pattern = re.compile(
            r'^//(\w+)\s+JOB\s+(.*)$',
            re.MULTILINE | re.IGNORECASE
        )
        
        lines = content.split('\n')
        jobs = []
        
        for i, line in enumerate(lines, 1):
            # Skip comments
            if self._is_comment_line(line):
                continue
            
            match = job_pattern.search(line)
            if match:
                job_name = match.group(1)
                job_params = match.group(2).strip()
                
                # Find job end (next job or end of file)
                line_end = self._find_job_end(lines, i - 1) + 1
                
                node = CodeNode(
                    node_type=NodeType.JOB,
                    name=job_name,
                    line_start=i,
                    line_end=line_end
                )
                
                # Extract job parameters
                self._extract_job_parameters(job_params, node)
                
                # Calculate complexity based on number of steps
                node.complexity = self._calculate_cyclomatic_complexity(content, i, line_end)
                
                result.nodes.append(node)
                jobs.append({'name': job_name, 'line': i, 'end': line_end})
                result.metadata.setdefault('jobs', []).append(jobs[-1])
                logger.debug(f"Found JCL job: {job_name} (lines {i}-{line_end})")
    
    def _parse_steps(self, content: str, result: ParseResult) -> None:
        """Parse JCL step statements with enhanced program/proc resolution."""
        # JCL steps start with //stepname EXEC
        step_pattern = re.compile(
            r'^//(\w+)\s+EXEC\s+(.*)$',
            re.MULTILINE | re.IGNORECASE
        )
        
        lines = content.split('\n')
        steps = []
        
        for i, line in enumerate(lines, 1):
            # Skip comments
            if self._is_comment_line(line):
                continue
            
            match = step_pattern.search(line)
            if match:
                step_name = match.group(1)
                exec_params = match.group(2).strip()
                
                # Find step end (next step, next job, or end of file)
                line_end = self._find_step_end(lines, i - 1, steps) + 1
                
                node = CodeNode(
                    node_type=NodeType.STEP,
                    name=step_name,
                    line_start=i,
                    line_end=line_end
                )
                
                # Extract program name if present
                prog_match = re.search(r'PGM=([A-Z0-9]+)', exec_params, re.IGNORECASE)
                if prog_match:
                    program = prog_match.group(1).upper()
                    node.metadata['program'] = program
                    node.metadata['exec_type'] = 'program'
                    if program not in result.dependencies:
                        result.dependencies.append(program)
                
                # Extract procedure name if present (can be PROC= or just procedure name)
                proc_match = re.search(r'(?:PROC=)?([A-Z0-9]+)', exec_params, re.IGNORECASE)
                if proc_match and not prog_match:
                    procedure = proc_match.group(1).upper()
                    # Check if it's not a parameter
                    if '=' not in procedure:
                        node.metadata['procedure'] = procedure
                        node.metadata['exec_type'] = 'procedure'
                        if procedure not in result.dependencies:
                            result.dependencies.append(procedure)
                
                # Extract COND parameter (conditional execution)
                cond_match = re.search(r'COND=\(([^)]+)\)', exec_params, re.IGNORECASE)
                if cond_match:
                    node.metadata['condition'] = cond_match.group(1)
                
                # Extract PARM parameter
                parm_match = re.search(r'PARM=([^,\s]+)', exec_params, re.IGNORECASE)
                if parm_match:
                    node.metadata['parameters'] = parm_match.group(1)
                
                # Find parent job
                parent_job = self._find_parent_job(lines, i - 1)
                if parent_job:
                    node.parent = parent_job
                    node.metadata['job'] = parent_job
                
                result.nodes.append(node)
                steps.append((i, step_name, node))
                
                step_info = {
                    'name': step_name,
                    'line': i,
                    'end': line_end,
                    'type': node.metadata.get('exec_type', 'unknown')
                }
                if 'program' in node.metadata:
                    step_info['program'] = node.metadata['program']
                if 'procedure' in node.metadata:
                    step_info['procedure'] = node.metadata['procedure']
                
                result.metadata.setdefault('steps', []).append(step_info)
                logger.debug(f"Found JCL step: {step_name} (lines {i}-{line_end})")
    
    def _parse_dd_statements(self, content: str, result: ParseResult) -> None:
        """Parse JCL DD (Data Definition) statements with dataset relationships."""
        # DD statements define datasets
        dd_pattern = re.compile(
            r'^//(\w+)\s+DD\s+(.*)$',
            re.MULTILINE | re.IGNORECASE
        )
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Skip comments
            if self._is_comment_line(line):
                continue
            
            match = dd_pattern.search(line)
            if match:
                dd_name = match.group(1)
                dd_params = match.group(2).strip()
                
                # Handle continuation lines
                full_params = dd_params
                j = i
                while j < len(lines) and lines[j].rstrip().endswith(','):
                    j += 1
                    if j < len(lines):
                        full_params += ' ' + lines[j].strip()
                
                line_end = j + 1
                
                node = CodeNode(
                    node_type=NodeType.DD_STATEMENT,
                    name=dd_name,
                    line_start=i,
                    line_end=line_end
                )
                
                # Extract dataset name
                dsn_match = re.search(r'DSN=([^\s,)]+)', full_params, re.IGNORECASE)
                if dsn_match:
                    dataset = dsn_match.group(1).upper()
                    node.metadata['dataset'] = dataset
                    
                    # Track dataset relationships
                    dataset_info = {'name': dataset, 'dd_name': dd_name, 'line': i}
                    
                    # Check disposition (DISP parameter)
                    disp_match = re.search(r'DISP=\(([^)]+)\)', full_params, re.IGNORECASE)
                    if disp_match:
                        disp_parts = disp_match.group(1).split(',')
                        node.metadata['disposition'] = disp_parts[0].strip().upper()
                        dataset_info['disposition'] = node.metadata['disposition']
                    
                    result.metadata.setdefault('datasets', []).append(dataset_info)
                
                # Check for dummy dataset
                if 'DUMMY' in full_params.upper():
                    node.metadata['type'] = 'DUMMY'
                
                # Check for SYSOUT
                sysout_match = re.search(r'SYSOUT=([A-Z])', full_params, re.IGNORECASE)
                if sysout_match:
                    node.metadata['sysout'] = sysout_match.group(1).upper()
                    node.metadata['type'] = 'SYSOUT'
                
                # Check for referback
                if dd_params.startswith('*.'):
                    referback = dd_params[2:].split(',')[0]
                    node.metadata['referback'] = referback
                    node.metadata['type'] = 'REFERBACK'
                
                # Find parent step
                parent_step = self._find_parent_step(lines, i - 1)
                if parent_step:
                    node.parent = parent_step
                    node.metadata['step'] = parent_step
                
                result.nodes.append(node)
    
    def _parse_procs(self, content: str, result: ParseResult) -> None:
        """Parse JCL procedure definitions with parameters."""
        # Procedures start with //procname PROC
        proc_pattern = re.compile(
            r'^//(\w+)\s+PROC\s+(.*)$',
            re.MULTILINE | re.IGNORECASE
        )
        
        lines = content.split('\n')
        procs = []
        
        for i, line in enumerate(lines, 1):
            # Skip comments
            if self._is_comment_line(line):
                continue
            
            match = proc_pattern.search(line)
            if match:
                proc_name = match.group(1)
                proc_params = match.group(2).strip()
                
                # Find PEND (procedure end)
                line_end = self._find_pend(lines, i - 1) + 1
                
                node = CodeNode(
                    node_type=NodeType.PROCEDURE,
                    name=proc_name,
                    line_start=i,
                    line_end=line_end
                )
                
                # Extract symbolic parameters
                if proc_params:
                    params = self._extract_symbolic_parameters(proc_params)
                    if params:
                        node.metadata['parameters'] = params
                
                # Calculate complexity
                node.complexity = self._calculate_cyclomatic_complexity(content, i, line_end)
                
                result.nodes.append(node)
                procs.append({'name': proc_name, 'line': i, 'end': line_end})
                result.metadata.setdefault('procedures', []).append(procs[-1])
                logger.debug(f"Found JCL procedure: {proc_name} (lines {i}-{line_end})")
    
    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a JCL comment (enhanced detection)."""
        if not line:
            return False
        
        stripped = line.strip()
        
        # Empty lines
        if not stripped:
            return False
        
        # JCL comments start with //*
        if stripped.startswith('//*'):
            return True
        
        # Also check for /* ... */ style comments (less common)
        if stripped.startswith('/*') and not stripped.startswith('//'):
            return True
        
        return False
    
    def _find_job_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a JCL job."""
        # Look for next JOB statement or end of file
        for i in range(start_idx + 1, len(lines)):
            if re.match(r'^//\w+\s+JOB\s+', lines[i], re.IGNORECASE):
                return i - 1
        return len(lines) - 1
    
    def _find_step_end(self, lines: List[str], start_idx: int, steps: List) -> int:
        """Find the end of a JCL step."""
        # Look for next EXEC, next JOB, or end of file
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if re.match(r'^//\w+\s+EXEC\s+', line, re.IGNORECASE):
                return i - 1
            if re.match(r'^//\w+\s+JOB\s+', line, re.IGNORECASE):
                return i - 1
        return len(lines) - 1
    
    def _find_pend(self, lines: List[str], start_idx: int) -> int:
        """Find PEND statement (end of procedure)."""
        pend_pattern = re.compile(r'^\s*PEND\s*$', re.IGNORECASE)
        for i in range(start_idx + 1, len(lines)):
            if pend_pattern.match(lines[i].strip()):
                return i
        return len(lines) - 1
    
    def _find_parent_job(self, lines: List[str], line_num: int) -> Optional[str]:
        """Find the parent job for a given line."""
        job_pattern = re.compile(r'^//(\w+)\s+JOB\s+', re.IGNORECASE)
        
        for i in range(line_num, -1, -1):
            match = job_pattern.search(lines[i])
            if match:
                return match.group(1)
        
        return None
    
    def _find_parent_step(self, lines: List[str], line_num: int) -> Optional[str]:
        """Find the parent step for a given line."""
        step_pattern = re.compile(r'^//(\w+)\s+EXEC\s+', re.IGNORECASE)
        
        for i in range(line_num, -1, -1):
            # Stop at job boundary
            if re.match(r'^//\w+\s+JOB\s+', lines[i], re.IGNORECASE):
                break
            
            match = step_pattern.search(lines[i])
            if match:
                return match.group(1)
        
        return None
    
    def _extract_job_parameters(self, params: str, node: CodeNode) -> None:
        """Extract job parameters from JOB statement."""
        # Extract accounting information (first parameter)
        if params:
            parts = params.split(',', 1)
            if parts:
                node.metadata['accounting'] = parts[0].strip('()')
        
        # Extract CLASS
        class_match = re.search(r'CLASS=([A-Z0-9])', params, re.IGNORECASE)
        if class_match:
            node.metadata['class'] = class_match.group(1).upper()
        
        # Extract MSGCLASS
        msgclass_match = re.search(r'MSGCLASS=([A-Z0-9])', params, re.IGNORECASE)
        if msgclass_match:
            node.metadata['msgclass'] = msgclass_match.group(1).upper()
        
        # Extract MSGLEVEL
        msglevel_match = re.search(r'MSGLEVEL=\(([^)]+)\)', params, re.IGNORECASE)
        if msglevel_match:
            node.metadata['msglevel'] = msglevel_match.group(1)
    
    def _extract_symbolic_parameters(self, params: str) -> Dict[str, str]:
        """Extract symbolic parameters from PROC statement."""
        param_dict = {}
        # Match patterns like PARAM1=VALUE1,PARAM2=VALUE2
        param_pattern = re.compile(r'([A-Z0-9]+)=([^,\s]+)', re.IGNORECASE)
        
        for match in param_pattern.finditer(params):
            param_name = match.group(1).upper()
            param_value = match.group(2)
            param_dict[param_name] = param_value
        
        return param_dict

# Made with Bob
