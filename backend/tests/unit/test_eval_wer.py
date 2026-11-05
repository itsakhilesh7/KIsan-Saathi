"""Unit tests for speech evaluation logic (WER/CER normalization and Hinglish intent evaluation)."""

import jiwer

from backend.app.services.intent_service import extract_intent
from backend.scripts.eval_wer import normalize_text


def test_hin02_identical_normalization_gives_zero_wer_and_cer():
    """Verify HIN-02 identical words with different punctuation yields exactly 0 WER and 0 CER."""
    # Reference with purna viram (danda) and question mark
    ref = "अगले दो दिनों में बारिश होने की संभावना है क्या? मुझे अपनी फसल की सिंचाई की योजना बनानी है।"
    # Hypothesis with same words, differing only in punctuation/whitespace
    hyp = "अगले दो दिनों में बारिश होने की संभावना है क्या? मुझे अपनी फसल की सिंचाई की योजना बनानी है"

    ref_norm = normalize_text(ref)
    hyp_norm = normalize_text(hyp)

    assert ref_norm == hyp_norm, f"Normalized strings should be identical: {ref_norm!r} != {hyp_norm!r}"

    wer_score = jiwer.wer(ref_norm, hyp_norm)
    cer_score = jiwer.cer(ref_norm, hyp_norm)

    # When WER is 0, CER MUST be 0
    assert wer_score == 0.0, f"Expected WER 0.0, got {wer_score}"
    assert cer_score == 0.0, f"Expected CER 0.0, got {cer_score}"


def test_wer_zero_mathematically_guarantees_cer_zero():
    """Any identical normalized string pair MUST have both WER 0.0 and CER 0.0."""
    test_pairs = [
        ("ఈరోజు టమాటా ధర ఎంత ఉంది?", "ఈరోజు టమాటా ధర ఎంత ఉంది"),
        ("आज मंडी में गेहूं का भाव कितना है।", "आज मंडी में गेहूं का भाव कितना है"),
        ("What is the mandi price today?", "what is the mandi price today?"),
    ]
    for r, h in test_pairs:
        rn = normalize_text(r)
        hn = normalize_text(h)
        assert rn == hn
        wer = jiwer.wer(rn, hn)
        cer = jiwer.cer(rn, hn)
        assert wer == 0.0
        assert cer == 0.0


def test_hinglish_evaluated_by_intent_and_slot_extraction():
    """Hinglish Roman references cannot be scored via character-distance WER against Devanagari STT.
    Verify that intent extraction correctly identifies the user's intent from the Devanagari transcript.
    """
    # Real HING-01 recognized hypothesis from Gnani STT (Devanagari phonetics)
    hing01_hyp = "कल मेरे विलेज में रेन होने के चांसेस क्या है? मुझे डिसाइड करना है कि इरीगेशन करना चाहिए या नहीं।"
    parsed01 = extract_intent(hing01_hyp)
    # Expected intent for HING-01 is weather_query
    assert parsed01.intent == "weather_query"

    # Real HING-02 recognized hypothesis from Gnani STT (crop problem)
    hing02_hyp = "मेरे टमेटो प्लांट के लीव्स कर्ल हो रहे हैं और ग्रोथ भी स्लो है, इसका पॉसिबल रीज़न क्या हो सकता है?"
    parsed02 = extract_intent(hing02_hyp, enable_crop_advisory=True)
    # Expected intent for HING-02 is crop_advisory_query
    assert parsed02.intent == "crop_advisory_query"
