import unittest
from unittest.mock import patch, MagicMock
import requests

from constants import DEFAULT_POSITIVE_DOMAINS
from fetcher import (
    fetch_hf_trending_papers,
    get_positive_domains,
    fetch_ai_news,
)


class TestConstantsAndConfig(unittest.TestCase):
    def test_positive_domains_contains_dair_and_hf(self):
        self.assertIn("academy.dair.ai", DEFAULT_POSITIVE_DOMAINS)
        self.assertIn("dair.ai", DEFAULT_POSITIVE_DOMAINS)
        self.assertIn("huggingface.co", DEFAULT_POSITIVE_DOMAINS)

    def test_get_positive_domains_returns_dair(self):
        domains = get_positive_domains()
        self.assertIn("academy.dair.ai", domains)


class TestFetchHFTrendingPapersUnit(unittest.TestCase):
    @patch("fetcher.requests.get")
    def test_successful_fetch_sorted_by_upvotes(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "paper": {"id": "2601.0001", "title": "Paper Baixo Voto", "upvotes": 5, "summary": "Sum 1"},
                "publishedAt": "2026-10-01"
            },
            {
                "paper": {"id": "2601.0002", "title": "Paper Alto Voto", "upvotes": 42, "summary": "Sum 2"},
                "publishedAt": "2026-10-02"
            },
            {
                "paper": {"id": "2601.0003", "title": "Paper Médio Voto", "upvotes": 15, "summary": "Sum 3"},
                "publishedAt": "2026-10-03"
            }
        ]
        mock_get.return_value = mock_response

        papers = fetch_hf_trending_papers(limit=2)
        self.assertEqual(len(papers), 2)
        # Deve estar ordenado decrescente por upvotes: 42 depois 15
        self.assertIn("Paper Alto Voto", papers[0]["title"])
        self.assertIn("42 votos", papers[0]["title"])
        self.assertEqual(papers[0]["link"], "https://huggingface.co/papers/2601.0002")
        self.assertIn("Paper Médio Voto", papers[1]["title"])

    @patch("fetcher.requests.get")
    def test_limit_zero_or_negative(self, mock_get):
        papers_zero = fetch_hf_trending_papers(limit=0)
        papers_neg = fetch_hf_trending_papers(limit=-3)
        self.assertEqual(papers_zero, [])
        self.assertEqual(papers_neg, [])
        mock_get.assert_not_called()

    @patch("fetcher.requests.get")
    def test_non_list_payload(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_get.return_value = mock_response

        papers = fetch_hf_trending_papers(limit=5)
        self.assertEqual(papers, [])

    @patch("fetcher.requests.get")
    def test_malformed_and_null_items(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            None,
            "string_invalida",
            {"paper": None, "publishedAt": None},
            {"paper": {"title": None, "id": None, "upvotes": None}},
            {"paper": {"id": "2601.9999", "title": "Valido", "upvotes": 10}}
        ]
        mock_get.return_value = mock_response

        papers = fetch_hf_trending_papers(limit=5)
        self.assertTrue(len(papers) >= 1)
        # Verifica que o item válido foi processado sem crash
        valid_entry = next((p for p in papers if "Valido" in p["title"]), None)
        self.assertIsNotNone(valid_entry)
        self.assertEqual(valid_entry["link"], "https://huggingface.co/papers/2601.9999")

    @patch("fetcher.requests.get")
    def test_http_error_handling(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        papers = fetch_hf_trending_papers(limit=5)
        self.assertEqual(papers, [])

    @patch("fetcher.requests.get")
    def test_network_exception_handling(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        papers = fetch_hf_trending_papers(limit=5)
        self.assertEqual(papers, [])


class TestFetchAiNewsWorkflow(unittest.TestCase):
    @patch("fetcher.fetch_hf_trending_papers")
    @patch("fetcher.fetch_rss")
    def test_fetch_ai_news_integration_and_deduplication(self, mock_fetch_rss, mock_fetch_hf):
        # Simula retornos das chamadas RSS
        mock_fetch_rss.side_effect = [
            # 1. brazil
            [{"title": "BR 1", "link": "https://g1.globo.com/1", "published": "Ontem", "summary": "S1"}],
            # 2. exterior
            [{"title": "US 1", "link": "https://techcrunch.com/1", "published": "Ontem", "summary": "S2"}],
            # 3. juridico
            [{"title": "DIR 1", "link": "https://conjur.com.br/1", "published": "Ontem", "summary": "S3"}],
            # 4. fronteira
            [{"title": "MIT 1", "link": "https://csail.mit.edu/1", "published": "Ontem", "summary": "S4"}],
            # 5. dair
            [
                {"title": "DAIR 1", "link": "https://academy.dair.ai/papers/1", "published": "Ontem", "summary": "S5"},
                {"title": "DAIR Dup", "link": "https://academy.dair.ai/papers/1", "published": "Ontem", "summary": "S5"}  # link duplicado
            ]
        ]

        mock_fetch_hf.return_value = [
            {"title": "[Paper HF] HF 1 (50 votos)", "link": "https://huggingface.co/papers/1", "published": "Ontem", "summary": "S6"}
        ]

        articles = fetch_ai_news()
        
        # Garante que não há duplicatas de links
        links = [a["link"] for a in articles]
        self.assertEqual(len(links), len(set(links)))

        # Garante que temos artigos do HF e do DAIR
        hf_found = any("huggingface.co" in a["link"] for a in articles)
        dair_found = any("dair.ai" in a["link"] for a in articles)
        self.assertTrue(hf_found)
        self.assertTrue(dair_found)

        # Garante o contrato de campos esperados por main.py e summarizer.py
        for a in articles:
            self.assertIn("title", a)
            self.assertIn("link", a)
            self.assertIn("published", a)
            self.assertIn("summary", a)


class TestLiveApiConnectivity(unittest.TestCase):
    def test_live_hf_trending_papers(self):
        """Teste de integração real com a API pública do Hugging Face"""
        papers = fetch_hf_trending_papers(limit=3)
        self.assertIsInstance(papers, list)
        self.assertEqual(len(papers), 3)
        for p in papers:
            self.assertTrue(p["link"].startswith("https://huggingface.co/papers"))
            self.assertTrue(p["title"].startswith("[Paper HF]"))
            self.assertIsInstance(p["summary"], str)
            self.assertIsInstance(p["published"], str)


class TestSummarizerWorkflow(unittest.TestCase):
    @patch("summarizer.genai.Client")
    @patch("summarizer.shorten_url", side_effect=lambda u: f" {u} ")
    def test_summarizer_prompt_contains_papers(self, mock_shorten, mock_client_cls):
        from summarizer import summarize_news_for_whatsapp
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "STOP"
        mock_response.candidates = [mock_candidate]
        mock_response.text = "🚀 *BOLETIM IA GERADO COM SUCESSO*"
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        articles = [
            {"title": "[Paper HF] Test Paper (50 votos)", "link": "https://huggingface.co/papers/123", "published": "2026-10-06", "summary": "Abstract teste"},
            {"title": "Notícia Jurídica", "link": "https://conjur.com.br/teste", "published": "2026-10-05", "summary": "Texto teste"}
        ]

        result = summarize_news_for_whatsapp(articles)
        self.assertEqual(result, "🚀 *BOLETIM IA GERADO COM SUCESSO*")
        
        # Inspeciona o prompt enviado ao Gemini
        call_args = mock_client.models.generate_content.call_args
        prompt_user = call_args.kwargs["contents"]
        self.assertIn("[Paper HF] Test Paper", prompt_user)
        self.assertIn("papers acadêmicos de ponta", prompt_user)

    def test_summarizer_empty_articles(self):
        from summarizer import summarize_news_for_whatsapp
        result = summarize_news_for_whatsapp([])
        self.assertEqual(result, "Não encontrei notícias relevantes sobre IA Generativa nesta semana.")


if __name__ == "__main__":
    unittest.main()
