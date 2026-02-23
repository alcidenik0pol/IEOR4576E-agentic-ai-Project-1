"""Tests for the out-of-scope backstop."""

import pytest

from app.backstop import check_out_of_scope, get_category_names


class TestBackstop:
    """Test cases for out-of-scope detection."""

    def test_coding_help_detected(self):
        """Test that coding help requests are detected."""
        questions = [
            "Write me a Python script to scrape a website",
            "Can you code a function for me?",
            "Help me debug this code",
            "How do I implement a binary search?",
        ]
        for question in questions:
            is_oos, response = check_out_of_scope(question)
            assert is_oos, f"Should detect as out of scope: {question}"
            assert response is not None

    def test_hardware_advice_detected(self):
        """Test that hardware advice requests are detected."""
        questions = [
            "What GPU should I buy for ML?",
            "Can my RTX 3080 run Llama?",
            "How much VRAM do I need?",
        ]
        for question in questions:
            is_oos, response = check_out_of_scope(question)
            assert is_oos, f"Should detect as out of scope: {question}"

    def test_ml_education_detected(self):
        """Test that ML education requests are detected."""
        questions = [
            "How do I fine-tune a model?",
            "Explain attention mechanism",
            "What is a transformer?",
            "Teach me about neural networks",
        ]
        for question in questions:
            is_oos, response = check_out_of_scope(question)
            assert is_oos, f"Should detect as out of scope: {question}"

    def test_non_hf_models_detected(self):
        """Test that non-HF model questions are detected."""
        questions = [
            "Tell me about GPT-4",
            "What is ChatGPT?",
            "Compare this to Claude",
            "Explain how Gemini works",
        ]
        for question in questions:
            is_oos, response = check_out_of_scope(question)
            assert is_oos, f"Should detect as out of scope: {question}"

    def test_valid_questions_not_blocked(self):
        """Test that valid HF model questions are not blocked."""
        questions = [
            "What license does bert-base-uncased use?",
            "Which models are good for text generation?",
            "What are the most downloaded models?",
            "Find models under 10B parameters",
            "Compare MiniLM and MPNet",
        ]
        for question in questions:
            is_oos, response = check_out_of_scope(question)
            assert not is_oos, f"Should NOT detect as out of scope: {question}"
            assert response is None

    def test_get_category_names(self):
        """Test that we have 4+ categories as required."""
        names = get_category_names()
        assert len(names) >= 4
        assert "coding_help" in names
        assert "hardware_advice" in names
        assert "ml_education" in names
        assert "non_hf_models" in names
