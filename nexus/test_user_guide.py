"""
Tests for the user guide HTML page.
Validates structure, content, and accessibility.
"""

import re
from pathlib import Path


def test_user_guide_exists():
    """Test that user-guide.html exists."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    assert guide_path.exists(), "user-guide.html should exist"


def test_user_guide_has_valid_html():
    """Test that user-guide.html has valid HTML structure."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Check for essential HTML elements
    assert "<!DOCTYPE html>" in content
    assert "<html" in content
    assert "</html>" in content
    assert "<head>" in content
    assert "</head>" in content
    assert "<body>" in content
    assert "</body>" in content


def test_user_guide_has_title():
    """Test that user-guide.html has a proper title."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    assert "<title>" in content
    assert "Nexus Protocol" in content
    assert "User Guide" in content


def test_user_guide_has_main_sections():
    """Test that user-guide.html includes all main sections."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Check for main sections
    required_sections = [
        "What is Nexus",
        "Getting Started",
        "Choose Your Journey",
        "Step-by-Step Guides",
        "Safety",
        "FAQ",
    ]

    for section in required_sections:
        assert section in content, f"Section '{section}' should be present"


def test_user_guide_has_navigation():
    """Test that user-guide.html has quick navigation cards."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    assert "quick-nav" in content
    assert "nav-card" in content


def test_user_guide_has_user_paths():
    """Test user-guide.html includes beginner/intermediate/advanced paths."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    assert "Beginner" in content
    assert "Intermediate" in content
    assert "Advanced" in content
    assert "Just Exploring" in content
    assert "Contract Manager" in content
    assert "Developer" in content or "Power User" in content


def test_user_guide_links_to_other_interfaces():
    """Test that user-guide.html links to other Nexus interfaces."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Check for links to other pages
    assert 'chimera.html' in content
    assert 'withdraw.html' in content
    assert 'README.xml' in content or 'GOVERNANCE.md' in content


def test_user_guide_has_safety_warnings():
    """Test that user-guide.html includes safety warnings."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    safety_keywords = [
        "security",
        "safe",
        "warning",
        "audited",
        "testnet",
        "risk",
    ]

    # At least some safety keywords should be present (case-insensitive)
    content_lower = content.lower()
    found_keywords = [kw for kw in safety_keywords if kw in content_lower]
    assert len(found_keywords) >= 3, (
        "Should include safety warnings and guidance"
    )


def test_user_guide_has_metamask_instructions():
    """Test that user-guide.html includes MetaMask setup instructions."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    assert "MetaMask" in content
    assert "wallet" in content.lower()


def test_user_guide_has_faq_section():
    """Test that user-guide.html has an FAQ section with questions."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    assert "FAQ" in content or "Frequently Asked Questions" in content
    assert "faq-item" in content
    assert "faq-question" in content

    # Check for some expected FAQ topics
    faq_topics = [
        "What",
        "safe",
        "NGTT",
        "DAO",
    ]

    content_lower = content.lower()
    found_topics = [
        topic for topic in faq_topics if topic.lower() in content_lower
    ]
    assert len(found_topics) >= 3, "Should have multiple FAQ topics"


def test_user_guide_has_step_by_step_instructions():
    """Test that user-guide.html includes step-by-step guides."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Check for step indicators
    assert "step-number" in content
    assert "Guide 1" in content or "Guide" in content

    # Check for numbered steps
    step_pattern = r'<span class="step-number">(\d+)</span>'
    steps = re.findall(step_pattern, content)
    assert len(steps) >= 3, "Should have multiple numbered steps"


def test_user_guide_has_glossary():
    """Test that user-guide.html includes a glossary of terms."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Check for glossary or key terms
    glossary_terms = [
        "NGTT",
        "Smart Contract",
        "DAO",
        "Token",
    ]

    found_terms = [term for term in glossary_terms if term in content]
    assert len(found_terms) >= 2, "Should explain key terms"


def test_user_guide_has_action_buttons():
    """Test that user-guide.html has actionable buttons."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    assert "btn" in content
    assert '<a href=' in content

    # Check for call-to-action elements
    assert "Start" in content or "Get Started" in content or "Begin" in content


def test_user_guide_has_responsive_design():
    """Test that user-guide.html includes responsive CSS."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    assert "viewport" in content
    assert "@media" in content
    assert "max-width" in content


def test_user_guide_has_javascript():
    """Test that user-guide.html includes interactive JavaScript."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    assert "<script>" in content
    assert "function" in content

    # Check for interactive functions
    assert "scrollToSection" in content or "scroll" in content
    assert "toggleFaq" in content or "toggle" in content


def test_user_guide_mentions_governance():
    """Test that user-guide.html mentions governance structure."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    assert "FuzzysTodd" in content
    assert "governance" in content.lower() or "DAO" in content


def test_user_guide_has_visual_hierarchy():
    """Test that user-guide.html has proper heading structure."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Check for heading levels
    assert "<h1" in content
    assert "<h2" in content
    assert "<h3" in content

    # Check for proper nesting (h1 should come before h2)
    h1_pos = content.find("<h1")
    h2_pos = content.find("<h2")
    assert h1_pos < h2_pos, "H1 should come before H2"


def test_user_guide_warns_about_risks():
    """Test that user-guide.html prominently warns about risks."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    risk_warnings = [
        "real project",
        "not audited",
        "own research",
        "testnet",
    ]

    content_lower = content.lower()
    found_warnings = [w for w in risk_warnings if w in content_lower]
    assert len(found_warnings) >= 2, "Should have clear risk warnings"


def test_user_guide_accessibility_features():
    """Test that user-guide.html has accessibility features."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Check for lang attribute
    assert 'lang="en"' in content

    # Check for semantic HTML
    assert "<section" in content or "<article" in content

    # Check for descriptive text
    assert (
        "alt=" in content or len(content) > 5000
    )  # Either has alt text or substantial content


def test_user_guide_has_emojis_for_visual_appeal():
    """Test that user-guide.html uses emojis for better UX."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Check for emoji characters (common emoji ranges in unicode)
    emoji_pattern = r'[\U0001F300-\U0001F9FF]'
    emojis = re.findall(emoji_pattern, content)

    # Should have some emojis for visual appeal
    assert len(emojis) >= 5, "Should use emojis to make guide more engaging"


def test_user_guide_content_organization():
    """Test that user-guide.html content is well-organized."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Check for organizational structures
    assert "section" in content
    assert "container" in content or "wrapper" in content

    # Check for lists
    assert "<ul" in content or "<ol" in content
    assert "<li>" in content


def test_user_guide_has_external_resources():
    """Test that user-guide.html links to helpful external resources."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Should mention metamask.io
    assert "metamask.io" in content.lower() or "metamask" in content.lower()

    # Should have external links
    assert 'target="_blank"' in content


def test_user_guide_code_examples():
    """Test that user-guide.html includes code examples where appropriate."""
    guide_path = Path(__file__).parent.parent / "user-guide.html"
    content = guide_path.read_text()

    # Check for code tags for function names
    assert "<code>" in content
    assert "withdraw" in content.lower()  # Should mention withdrawal functions
