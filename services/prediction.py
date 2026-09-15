from . import market


def _verdict(score):
    if score >= 3:   return "STRONG BULLISH", "🚀", "Tinggi"
    if score >= 1:   return "BULLISH", "📈", "Sedang"
    if score == 0:   return "NEUTRAL", "⚖️", "Rendah"
    if score >= -2:  return "BEARISH", "📉", "Sedang"
    return "STRONG BEARISH", "🔻", "Tinggi"


async def predict(coin):
    score = 0
    reasons = []

    try:
        rsi = await market.get_rsi(coin, interval="4h", period=14)
        if rsi is None:
            reasons.append("RSI: data tidak cukup")
        elif rsi < 30:
            score += 2; reasons.append(f"RSI {rsi:.1f} oversold → potensi naik")
        elif rsi > 70:
            score -= 2; reasons.append(f"RSI {rsi:.1f} overbought → potensi koreksi")
        else:
            reasons.append(f"RSI {rsi:.1f} netral")
    except Exception as e:
        reasons.append(f"RSI: gagal ({e})")

    try:
        ma = await market.get_ma_cross(coin, interval="4h")
        m20, m50, m200 = ma.get("ma20"), ma.get("ma50"), ma.get("ma200")
        if m20 is not None and m50 is not None:
            if m20 > m50:
                score += 1; reasons.append("MA20 > MA50 → bullish")
            else:
                score -= 1; reasons.append("MA20 < MA50 → bearish")
        if m50 is not None and m200 is not None:
            if m50 > m200:
                score += 1; reasons.append("MA50 > MA200 → golden cross")
            else:
                score -= 1; reasons.append("MA50 < MA200 → death cross")
    except Exception as e:
        reasons.append(f"MA: gagal ({e})")

    try:
        fg = await market.get_fear_greed()
        val = fg["value"]
        if val < 25:
            score += 1; reasons.append(f"F&G {val} → peluang beli")
        elif val > 75:
            score -= 1; reasons.append(f"F&G {val} → hati-hati")
        else:
            reasons.append(f"F&G {val} netral")
    except Exception as e:
        reasons.append(f"F&G: gagal ({e})")

    try:
        fund = await market.get_funding(coin)
        f = fund["funding"]
        if f > 0.05:
            score -= 1; reasons.append(f"Funding {f:.3f}% → long crowded")
        elif f < -0.03:
            score += 1; reasons.append(f"Funding {f:.3f}% → short crowded")
        else:
            reasons.append(f"Funding {f:.3f}% netral")
    except Exception as e:
        reasons.append(f"Funding: gagal ({e})")

    try:
        price = await market.get_price(coin)
        ch = price.get("change_24h")
        if ch is not None:
            if ch > 5:
                score += 1; reasons.append(f"24h {ch:+.2f}% → momentum kuat")
            elif ch < -5:
                score -= 1; reasons.append(f"24h {ch:+.2f}% → momentum lemah")
            else:
                reasons.append(f"24h {ch:+.2f}% netral")
    except Exception as e:
        reasons.append(f"24h: gagal ({e})")

    verdict, emoji, confidence = _verdict(score)
    return {"coin": coin, "score": score, "verdict": verdict,
            "emoji": emoji, "confidence": confidence, "reasons": reasons}