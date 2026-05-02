# for IBM hackathon
"""
Modernization Agent using LangGraph.

This module implements the main agent that orchestrates the 8-stage
analysis workflow using LangGraph's StateGraph.
"""

import logging
from typing import Any, Dict, List

from langgraph.graph import END, StateGraph

from app.agents.agent_nodes import (
    analyze_node,
    classify_node,
    explain_node,
    ingest_node,
    parse_node,
    recommend_node,
    report_node,
    validate_node,
)
from app.agents.agent_state import AgentState, FileInfo, create_initial_state

logger = logging.getLogger(__name__)


class ModernizationAgent:
    """
    AI-powered modernization agent using LangGraph.
    
    This agent orchestrates an 8-stage workflow:
    1. Ingest - Load and validate files
    2. Parse - Extract code structure
    3. Classify - Categorize files and components
    4. Analyze - Detect risks and patterns
    5. Explain - Generate human-readable explanations
    6. Recommend - Generate modernization suggestions
    7. Validate - Verify recommendations
    8. Report - Generate final report
    """

    def __init__(self):
        """Initialize the modernization agent with LangGraph workflow."""
        self.graph = self._build_graph()
        logger.info("ModernizationAgent initialized")

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph for the analysis workflow.
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes for each stage
        workflow.add_node("ingest", ingest_node)
        workflow.add_node("parse", parse_node)
        workflow.add_node("classify", classify_node)
        workflow.add_node("analyze", analyze_node)
        workflow.add_node("explain", explain_node)
        workflow.add_node("recommend", recommend_node)
        workflow.add_node("validate", validate_node)
        workflow.add_node("report", report_node)

        # Define the workflow edges (linear flow)
        workflow.set_entry_point("ingest")
        workflow.add_edge("ingest", "parse")
        workflow.add_edge("parse", "classify")
        workflow.add_edge("classify", "analyze")
        workflow.add_edge("analyze", "explain")
        workflow.add_edge("explain", "recommend")
        workflow.add_edge("recommend", "validate")
        workflow.add_edge("validate", "report")
        workflow.add_edge("report", END)

        # Compile the graph
        return workflow.compile()

    async def analyze(
        self,
        job_id: str,
        uploaded_files: List[FileInfo],
        analysis_config: Dict[str, Any],
    ) -> AgentState:
        """
        Run the complete analysis workflow.
        
        Args:
            job_id: Unique job identifier
            uploaded_files: List of uploaded files to analyze
            analysis_config: Analysis configuration options
        
        Returns:
            Final agent state with complete analysis results
        """
        logger.info(f"[Job {job_id}] Starting modernization analysis")
        logger.info(f"[Job {job_id}] Files: {len(uploaded_files)}, Config: {analysis_config}")

        try:
            # Create initial state
            initial_state = create_initial_state(
                job_id=job_id,
                uploaded_files=uploaded_files,
                analysis_config=analysis_config,
            )

            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)

            logger.info(
                f"[Job {job_id}] Analysis complete. "
                f"Status: {final_state.get('status')}, "
                f"Progress: {final_state.get('progress_percent')}%"
            )

            return final_state

        except Exception as e:
            logger.error(f"[Job {job_id}] Analysis failed: {e}", exc_info=True)
            raise

    def analyze_sync(
        self,
        job_id: str,
        uploaded_files: List[FileInfo],
        analysis_config: Dict[str, Any],
    ) -> AgentState:
        """
        Run the complete analysis workflow (synchronous version).
        
        Args:
            job_id: Unique job identifier
            uploaded_files: List of uploaded files to analyze
            analysis_config: Analysis configuration options
        
        Returns:
            Final agent state with complete analysis results
        """
        logger.info(f"[Job {job_id}] Starting modernization analysis (sync)")

        try:
            # Create initial state
            initial_state = create_initial_state(
                job_id=job_id,
                uploaded_files=uploaded_files,
                analysis_config=analysis_config,
            )

            # Run the workflow synchronously
            final_state = self.graph.invoke(initial_state)

            logger.info(
                f"[Job {job_id}] Analysis complete. "
                f"Status: {final_state.get('status')}"
            )

            return final_state

        except Exception as e:
            logger.error(f"[Job {job_id}] Analysis failed: {e}", exc_info=True)
            raise

    async def analyze_stream(
        self,
        job_id: str,
        uploaded_files: List[FileInfo],
        analysis_config: Dict[str, Any],
    ):
        """
        Run the analysis workflow with streaming updates.
        
        This allows monitoring progress as each stage completes.
        
        Args:
            job_id: Unique job identifier
            uploaded_files: List of uploaded files to analyze
            analysis_config: Analysis configuration options
        
        Yields:
            Agent state after each stage completion
        """
        logger.info(f"[Job {job_id}] Starting modernization analysis (streaming)")

        try:
            # Create initial state
            initial_state = create_initial_state(
                job_id=job_id,
                uploaded_files=uploaded_files,
                analysis_config=analysis_config,
            )

            # Stream the workflow execution
            async for state in self.graph.astream(initial_state):
                current_stage = state.get("current_stage", "unknown")
                progress = state.get("progress_percent", 0)
                
                logger.info(
                    f"[Job {job_id}] Stage update: {current_stage} ({progress}%)"
                )
                
                yield state

        except Exception as e:
            logger.error(f"[Job {job_id}] Analysis streaming failed: {e}", exc_info=True)
            raise

    def get_workflow_visualization(self) -> str:
        """
        Get a visual representation of the workflow graph.
        
        Returns:
            Mermaid diagram of the workflow
        """
        return """
        graph TD
            START([Start]) --> INGEST[1. Ingest]
            INGEST --> PARSE[2. Parse]
            PARSE --> CLASSIFY[3. Classify]
            CLASSIFY --> ANALYZE[4. Analyze]
            ANALYZE --> EXPLAIN[5. Explain]
            EXPLAIN --> RECOMMEND[6. Recommend]
            RECOMMEND --> VALIDATE[7. Validate]
            VALIDATE --> REPORT[8. Report]
            REPORT --> END([End])
            
            style INGEST fill:#e1f5ff
            style PARSE fill:#e1f5ff
            style CLASSIFY fill:#fff4e1
            style ANALYZE fill:#fff4e1
            style EXPLAIN fill:#e8f5e9
            style RECOMMEND fill:#e8f5e9
            style VALIDATE fill:#f3e5f5
            style REPORT fill:#f3e5f5
        """


# Global agent instance (singleton)
_agent_instance: ModernizationAgent = None


def get_agent() -> ModernizationAgent:
    """
    Get the global ModernizationAgent instance (singleton pattern).
    
    Returns:
        ModernizationAgent instance
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ModernizationAgent()
    return _agent_instance

# Made with Bob
