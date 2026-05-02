"""
Test IBM watsonx.ai Integration

Tests for the watsonx.ai provider and integration with the LLM chain.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from app.llm.watsonx_provider import WatsonxProvider
from app.llm.provider_chain import LLMProviderChain, get_llm_chain
from app.llm.base_provider import LLMResponse


class TestWatsonxProvider:
    """Test watsonx.ai provider functionality."""
    
    @pytest.fixture
    def provider(self):
        """Create a watsonx provider instance."""
        return WatsonxProvider()
    
    def test_provider_initialization(self, provider):
        """Test provider initializes with correct name and model."""
        assert provider.name == "watsonx"
        assert provider.model is not None
        assert not provider.available  # Not available until check_availability
    
    @pytest.mark.asyncio
    async def test_check_availability_without_credentials(self, provider):
        """Test availability check fails without credentials."""
        with patch('app.config.settings.settings') as mock_settings:
            mock_settings.watsonx_api_key = "your-watsonx-api-key-here"
            mock_settings.watsonx_project_id = "your-project-id-here"
            
            available = await provider.check_availability()
            assert not available
            assert not provider.available
    
    @pytest.mark.asyncio
    async def test_check_availability_with_credentials(self, provider):
        """Test availability check succeeds with valid credentials."""
        with patch('app.config.settings.settings') as mock_settings:
            mock_settings.watsonx_api_key = "valid-api-key"
            mock_settings.watsonx_project_id = "valid-project-id"
            mock_settings.watsonx_url = "https://us-south.ml.cloud.ibm.com"
            mock_settings.watsonx_model = "ibm/granite-13b-chat-v2"
            
            with patch('app.llm.watsonx_provider.Model') as mock_model:
                mock_model.return_value = Mock()
                
                available = await provider.check_availability()
                assert available
                assert provider.available
    
    @pytest.mark.asyncio
    async def test_generate_without_availability(self, provider):
        """Test generate returns error when provider not available."""
        response = await provider.generate("Test prompt")
        
        assert not response.success
        assert response.error is not None
        assert "not available" in response.error.lower()
        assert response.provider == "watsonx"
    
    @pytest.mark.asyncio
    async def test_generate_with_mock_model(self, provider):
        """Test generate with mocked watsonx model."""
        # Setup mock
        mock_model = Mock()
        mock_model.generate_text.return_value = {
            "results": [{
                "generated_text": "This is a test response",
                "generated_token_count": 10,
                "input_token_count": 5
            }]
        }
        
        provider.model_instance = mock_model
        provider.available = True
        provider.gen_params = {}
        
        # Test generation
        response = await provider.generate(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant"
        )
        
        assert response.success
        assert response.content == "This is a test response"
        assert response.tokens_used == 15  # 10 + 5
        assert response.provider == "watsonx"
        assert response.model == provider.model
    
    @pytest.mark.asyncio
    async def test_generate_with_parameters(self, provider):
        """Test generate respects custom parameters."""
        mock_model = Mock()
        mock_model.generate_text.return_value = "Response"
        
        provider.model_instance = mock_model
        provider.available = True
        provider.gen_params = {}
        
        response = await provider.generate(
            prompt="Test",
            temperature=0.5,
            max_tokens=1000,
            top_p=0.9,
            top_k=40
        )
        
        # Verify model was called
        mock_model.generate_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_handles_exceptions(self, provider):
        """Test generate handles exceptions gracefully."""
        mock_model = Mock()
        mock_model.generate_text.side_effect = Exception("API Error")
        
        provider.model_instance = mock_model
        provider.available = True
        provider.gen_params = {}
        
        response = await provider.generate("Test prompt")
        
        assert not response.success
        assert "API Error" in response.error
        assert response.latency_ms > 0


class TestProviderChain:
    """Test LLM provider chain with watsonx.ai."""
    
    @pytest.fixture
    def chain(self):
        """Create a provider chain instance."""
        return LLMProviderChain()
    
    def test_chain_initialization(self, chain):
        """Test chain initializes with watsonx as first provider."""
        assert len(chain.providers) == 4
        assert chain.providers[0].name == "watsonx"
        assert chain.providers[1].name == "openai"
        assert chain.providers[2].name == "groq"
        assert chain.providers[3].name == "rule-based"
    
    @pytest.mark.asyncio
    async def test_chain_prioritizes_watsonx(self, chain):
        """Test chain tries watsonx first."""
        # Mock watsonx as available and successful
        with patch.object(chain.providers[0], 'check_availability', 
                         return_value=True):
            with patch.object(chain.providers[0], 'is_available', 
                            return_value=True):
                with patch.object(chain.providers[0], 'generate',
                                return_value=LLMResponse(
                                    content="watsonx response",
                                    provider="watsonx",
                                    model="granite",
                                    success=True
                                )):
                    
                    response = await chain.generate("Test prompt")
                    
                    assert response.success
                    assert response.provider == "watsonx"
                    assert response.content == "watsonx response"
    
    @pytest.mark.asyncio
    async def test_chain_falls_back_to_openai(self, chain):
        """Test chain falls back to OpenAI when watsonx fails."""
        # Mock watsonx as unavailable
        with patch.object(chain.providers[0], 'is_available', 
                         return_value=False):
            # Mock OpenAI as available
            with patch.object(chain.providers[1], 'is_available',
                            return_value=True):
                with patch.object(chain.providers[1], 'generate',
                                return_value=LLMResponse(
                                    content="openai response",
                                    provider="openai",
                                    model="gpt-4",
                                    success=True
                                )):
                    
                    response = await chain.generate("Test prompt")
                    
                    assert response.success
                    assert response.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_chain_initialization_checks_all_providers(self, chain):
        """Test initialization checks all providers."""
        with patch.object(chain.providers[0], 'check_availability',
                         return_value=True) as mock_watsonx:
            with patch.object(chain.providers[1], 'check_availability',
                            return_value=True) as mock_openai:
                with patch.object(chain.providers[2], 'check_availability',
                                return_value=True) as mock_groq:
                    with patch.object(chain.providers[3], 'check_availability',
                                    return_value=True) as mock_rule:
                        
                        await chain.initialize()
                        
                        mock_watsonx.assert_called_once()
                        mock_openai.assert_called_once()
                        mock_groq.assert_called_once()
                        mock_rule.assert_called_once()
    
    def test_get_available_providers(self, chain):
        """Test getting list of available providers."""
        chain.providers[0].available = True
        chain.providers[1].available = False
        chain.providers[2].available = True
        chain.providers[3].available = True
        
        available = chain.get_available_providers()
        
        assert "watsonx" in available
        assert "openai" not in available
        assert "groq" in available
        assert "rule-based" in available
    
    def test_get_provider_status(self, chain):
        """Test getting provider status."""
        chain.providers[0].available = True
        chain.providers[1].available = False
        
        status = chain.get_provider_status()
        
        assert "watsonx" in status
        assert status["watsonx"]["available"] is True
        assert "openai" in status
        assert status["openai"]["available"] is False


class TestWatsonxOrchestrate:
    """Test watsonx Orchestrate integration."""
    
    @pytest.fixture
    def provider(self):
        """Create a watsonx provider instance."""
        return WatsonxProvider()
    
    @pytest.mark.asyncio
    async def test_orchestrate_fallback_to_standard(self, provider):
        """Test Orchestrate falls back to standard generation."""
        mock_model = Mock()
        mock_model.generate_text.return_value = "Response"
        
        provider.model_instance = mock_model
        provider.available = True
        provider.gen_params = {}
        
        response = await provider.generate_with_orchestrate(
            prompt="Test prompt",
            workflow_id="test-workflow"
        )
        
        # Should fall back to standard generation
        assert response.provider == "watsonx"


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_code_analysis_workflow(self):
        """Test complete code analysis workflow."""
        chain = LLMProviderChain()
        
        # Mock watsonx as available
        with patch.object(chain.providers[0], 'is_available',
                         return_value=True):
            with patch.object(chain.providers[0], 'generate',
                            return_value=LLMResponse(
                                content="Code analysis: This is a COBOL program...",
                                provider="watsonx",
                                model="granite",
                                success=True,
                                tokens_used=150
                            )):
                
                # Simulate code analysis
                code = "IDENTIFICATION DIVISION..."
                prompt = f"Analyze this COBOL code: {code}"
                
                response = await chain.generate(
                    prompt=prompt,
                    system_prompt="You are an expert in legacy code analysis"
                )
                
                assert response.success
                assert "Code analysis" in response.content
                assert response.provider == "watsonx"
    
    @pytest.mark.asyncio
    async def test_documentation_generation(self):
        """Test documentation generation workflow."""
        chain = LLMProviderChain()
        
        with patch.object(chain.providers[0], 'is_available',
                         return_value=True):
            with patch.object(chain.providers[0], 'generate',
                            return_value=LLMResponse(
                                content="# Documentation\n\nThis module handles...",
                                provider="watsonx",
                                model="granite",
                                success=True
                            )):
                
                response = await chain.generate(
                    prompt="Generate documentation for this code",
                    temperature=0.3  # Lower for factual content
                )
                
                assert response.success
                assert "Documentation" in response.content


def test_singleton_chain():
    """Test LLM chain singleton pattern."""
    chain1 = get_llm_chain()
    chain2 = get_llm_chain()
    
    assert chain1 is chain2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

# Made with Bob
