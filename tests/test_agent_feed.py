import os
import unittest
from unittest.mock import patch, MagicMock

from constants import (
    DEFAULT_AGENT_DOMAINS,
    SCHEDULE_TASK_NAME_AGENTS,
    SCHEDULE_TASK_NAME,
)
from fetcher import (
    get_agent_domains,
    fetch_agent_ai_news,
)
from summarizer import summarize_agent_news_for_whatsapp
from storage import save_summary_locally


class TestAgentConstantsAndDomains(unittest.TestCase):
    def test_default_agent_domains_has_at_least_15_sources(self):
        self.assertGreaterEqual(len(DEFAULT_AGENT_DOMAINS), 15)
        # Verifica as fontes de peso mundial
        self.assertIn("huggingface.co", DEFAULT_AGENT_DOMAINS)
        self.assertIn("academy.dair.ai", DEFAULT_AGENT_DOMAINS)
        self.assertIn("arxiv.org", DEFAULT_AGENT_DOMAINS)
        self.assertIn("openai.com", DEFAULT_AGENT_DOMAINS)
        self.assertIn("anthropic.com", DEFAULT_AGENT_DOMAINS)
        self.assertIn("deepmind.google", DEFAULT_AGENT_DOMAINS)
        self.assertIn("csail.mit.edu", DEFAULT_AGENT_DOMAINS)
        self.assertIn("hai.stanford.edu", DEFAULT_AGENT_DOMAINS)
        self.assertIn("bair.berkeley.edu", DEFAULT_AGENT_DOMAINS)
        self.assertIn("paperswithcode.com", DEFAULT_AGENT_DOMAINS)
        self.assertIn("nature.com", DEFAULT_AGENT_DOMAINS)
        self.assertIn("blog.langchain.dev", DEFAULT_AGENT_DOMAINS)

    def test_schedule_task_names_distinct(self):
        self.assertEqual(SCHEDULE_TASK_NAME, "BoletimIANews")
        self.assertEqual(SCHEDULE_TASK_NAME_AGENTS, "BoletimIAAgentes")
        self.assertNotEqual(SCHEDULE_TASK_NAME, SCHEDULE_TASK_NAME_AGENTS)

    def test_get_agent_domains_returns_list(self):
        domains = get_agent_domains()
        self.assertIsInstance(domains, list)
        self.assertGreaterEqual(len(domains), 15)


class TestFetchAgentAiNewsUnit(unittest.TestCase):
    @patch("fetcher.fetch_rss")
    @patch("fetcher.fetch_hf_trending_papers")
    def test_fetch_agent_ai_news_merging_and_deduplication(self, mock_hf, mock_rss):
        mock_hf.return_value = [
            {"title": "[Paper HF] Agent Reasoning (30 votos)", "link": "https://huggingface.co/papers/2601.1", "published": "Ontem", "summary": "HF Summary"}
        ]
        mock_rss.side_effect = [
            # 2. dair
            [
                {"title": "DAIR Agent 1", "link": "https://academy.dair.ai/papers/agent1", "published": "Ontem", "summary": "DAIR Sum"},
                {"title": "DAIR Dup", "link": "https://academy.dair.ai/papers/agent1", "published": "Ontem", "summary": "DAIR Sum"}
            ],
            # 3. lab_articles
            [
                {"title": "arXiv Multi-Agent", "link": "https://arxiv.org/abs/2601.2", "published": "Ontem", "summary": "arXiv Sum"}
            ],
            # 4. dev_articles
            [
                {"title": "LangChain Framework", "link": "https://blog.langchain.dev/agent-eval", "published": "Ontem", "summary": "LC Sum"}
            ],
            # 5. spec_articles
            [
                {"title": "The Gradient Deep Dive", "link": "https://thegradient.pub/agents", "published": "Ontem", "summary": "TG Sum"}
            ]
        ]

        articles = fetch_agent_ai_news()
        self.assertIsInstance(articles, list)
        self.assertEqual(len(articles), 5)  # 5 únicos (1 HF, 1 DAIR sem duplicata, 1 arXiv, 1 LangChain, 1 The Gradient)

        # Sem duplicatas de link
        links = [a["link"] for a in articles]
        self.assertEqual(len(links), len(set(links)))

        for art in articles:
            self.assertIn("title", art)
            self.assertIn("link", art)
            self.assertIn("published", art)
            self.assertIn("summary", art)


class TestSummarizerAgentWorkflow(unittest.TestCase):
    @patch("summarizer._call_gemini_with_fallback")
    @patch("summarizer.shorten_url", side_effect=lambda u: f" {u} ")
    def test_summarize_agent_news_prompt_construction(self, mock_shorten, mock_gemini_call):
        mock_gemini_call.return_value = "🤖 *BOLETIM TÉCNICO: AGENTES DE IA*"

        sample_articles = [
            {
                "title": f"[Paper HF] Paper Agente {i}",
                "link": f"https://huggingface.co/papers/{i}",
                "published": "2026-10-06",
                "summary": f"Resumo do paper de agente {i}"
            }
            for i in range(1, 20)
        ]

        result = summarize_agent_news_for_whatsapp(sample_articles)
        self.assertEqual(result, "🤖 *BOLETIM TÉCNICO: AGENTES DE IA*")

        mock_gemini_call.assert_called_once()
        client, prompt_user, prompt_system = mock_gemini_call.call_args[0]

        # Verifica regras essenciais do prompt técnico
        self.assertIn("15 PRINCIPAIS papers", prompt_user)
        self.assertIn("LINGUAGEM SIMPLES E DIDÁTICA", prompt_user)
        self.assertIn("INDICAÇÃO DE FONTE E LINK", prompt_user)
        self.assertIn("BOLETIM TÉCNICO: AGENTES DE IA", prompt_user)
        self.assertIn("Paper Agente 1", prompt_user)

    def test_summarize_agent_news_empty_list(self):
        result = summarize_agent_news_for_whatsapp([])
        self.assertEqual(result, "Não encontrei novidades ou papers relevantes sobre Agentes de IA nesta semana.")


class TestStoragePrefixSupport(unittest.TestCase):
    def test_save_summary_locally_with_agent_prefix(self):
        filepath = save_summary_locally("Conteúdo teste de agentes", prefix="boletim_ia_agentes")
        self.assertTrue(os.path.exists(filepath))
        basename = os.path.basename(filepath)
        self.assertTrue(basename.startswith("boletim_ia_agentes_"))
        self.assertTrue(basename.endswith(".md"))
        # Limpa arquivo temporário criado no teste
        try:
            os.remove(filepath)
        except OSError:
            pass


class TestLiveAgentNewsFetch(unittest.TestCase):
    def test_live_agent_news_returns_papers(self):
        """Teste de integração real coletando papers de agentes"""
        articles = fetch_agent_ai_news()
        self.assertIsInstance(articles, list)
        self.assertGreaterEqual(len(articles), 5)
        # Garante que temos papers do Hugging Face e DAIR entre os artigos retornados
        has_hf = any("huggingface.co" in a["link"] for a in articles)
        self.assertTrue(has_hf)


if __name__ == "__main__":
    unittest.main()
