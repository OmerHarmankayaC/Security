#!/usr/bin/env bash
# Yayin oncesi ucdan uca kontrol. SUNUCUDA kosar, hicbir sey yazmaz.
#
# Yaziyor gorunen tek adim `curl -X POST`tur ve o da KASITLIDIR: salt okunur
# kapisinin gercekten reddettigini kanitlamanin baska yolu yok. Istekler
# OTURUMSUZ atilir - kapi ara katmanda, yetkilendirmeden ONCE calisir, yani
# kapi ayaktaysa 403 doner. Kapi dusmusse istek yetkilendirmeye ulasir ve 401
# alir; yine hicbir sey yazilmaz ama BU BIR HATADIR ve tablo onu kirmizi
# gosterir.
#
# Kullanim:
#   sudo bash yayin_kontrolu.sh https://<alan-adi> [/opt/vardiya]

set -uo pipefail

ADRES="${1:?kullanim: yayin_kontrolu.sh <adres> [kurulum-dizini]}"
KURULUM="${2:-/opt/vardiya}"
ADRES="${ADRES%/}"

gecti=0
kaldi=0

# satir <baslik> <beklenen> <olculen>  — ucuncu argüman beklenene esitse gecer
satir() {
  local baslik="$1" beklenen="$2" olculen="$3"
  if [ "$beklenen" = "$olculen" ]; then
    printf '  [GECTI] %-38s %s\n' "$baslik" "$olculen"
    gecti=$((gecti + 1))
  else
    printf '  [KALDI] %-38s beklenen: %s | olculen: %s\n' "$baslik" "$beklenen" "$olculen"
    kaldi=$((kaldi + 1))
  fi
}

kod() { curl -sS -o /dev/null -w '%{http_code}' -m 20 "$@"; }
govde() { curl -sS -m 20 "$@"; }

# X-Robots-Tag yanitta BIRDEN COK kez bulunabilir ve bu dogrudur: statik
# icerige basligi vekil koyar, /api/* hem vekilden hem uygulamanin ara
# katmanindan gecer. Ayni degeri iki kez gormek bir kusur degil, README'de
# yazan iki katmanli kurulumun dogal sonucu - ve tekrarlanan ayni yonerge
# gezginler icin de tek yonergedir.
#
# Ilk surum satirlari oldugu gibi karsilastiriyordu; iki ayni satir tek
# satira esit olmadigi icin DOGRU KURULMUS bir sunucuyu "kaldi" gosterdi.
# Tekillestiriyoruz: degerler ayni ise o deger, farkli ise ikisi de basilir.
baslik() {
  curl -sS -D - -o /dev/null -m 20 "$1" \
    | sed -n 's/^[Xx]-[Rr]obots-[Tt]ag:[[:space:]]*//p' \
    | tr -d '\r' | sort -u | paste -sd' + ' -
}

echo "== Yayin kontrolu: $ADRES =="
echo

# --- 1. Demo kipi -----------------------------------------------------------
satir "DEMO_KIPI acik" "true" \
  "$(govde "$ADRES/api/ortam" | sed -n 's/.*"demo_kipi":[[:space:]]*\([a-z]*\).*/\1/p')"

# --- 2. Kimlik kutusu -------------------------------------------------------
KIMLIK="$(govde "$ADRES/api/demo/kimlik")"
satir "kimlik kutusu hesap sayisi" "4" \
  "$(printf '%s' "$KIMLIK" | grep -o '"kullanici_adi"' | wc -l | tr -d ' ')"
# Her hesabin KENDI parolasi olmali; ortak tek parola ESKI surumun izidir.
satir "her hesabin kendi parolasi" "4" \
  "$(printf '%s' "$KIMLIK" | grep -o '"parola"' | wc -l | tr -d ' ')"

# --- 3. Girisler ------------------------------------------------------------
for h in demo_idare demo_hesap demo_d1010 demo_d1020; do
  # JSON'u python ayristirir: elle `tr`/`sed` ile parcalamak, alan sirasi
  # degisir degismez sessizce bozuk parola uretiyordu (422 aliniyordu).
  p="$(printf '%s' "$KIMLIK" | python3 -c '
import json, sys
h = sys.argv[1]
try:
    v = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for k in v.get("hesaplar", []):
    if k.get("kullanici_adi") == h:
        print(k.get("parola", ""))
        break
' "$h")"
  if [ -z "$p" ]; then
    satir "giris: $h" "200" "parola alinamadi"
    continue
  fi
  # Govde AYRI BIR DEGISKENDE kurulur. Dogrudan `$(kod ... -d "{...}")`
  # icine yazildiginda ic ice tirnaklar govdeyi virgulden ikiye bolup iki
  # ayri `-d` argumani yapiyordu; istek 422 donuyor ve kontrol, CALISAN bir
  # girisi "kaldi" gosteriyordu. Yanlis alarm veren bir dogrulama, hic
  # olmayandan kotudur.
  govde_json="{\"kullanici_adi\":\"$h\",\"parola\":\"$p\"}"
  satir "giris: $h" "200" \
    "$(kod -X POST -H 'Content-Type: application/json' -d "$govde_json" "$ADRES/api/giris")"
done

# --- 4. Salt okunur kapisi --------------------------------------------------
# Oturumsuz POST: kapi ayaktaysa 403 (kapi yetkiden once), degilse 401.
for u in /api/personel /api/donem /api/gorev-noktasi; do
  satir "salt okunur reddi: $u" "403" \
    "$(kod -X POST -H 'Content-Type: application/json' -d '{}' "$ADRES$u")"
done
satir "salt okunur reddi: DELETE /api/surum/1" "403" \
  "$(kod -X DELETE "$ADRES/api/surum/1")"

# --- 5. Dizinlemeye kapali --------------------------------------------------
satir "robots.txt dosya olarak var" "yes" \
  "$(govde "$ADRES/robots.txt" | grep -qi '^User-agent' && echo yes || echo no)"
satir "X-Robots-Tag: /" "noindex, nofollow" "$(baslik "$ADRES/")"
satir "X-Robots-Tag: /api" "noindex, nofollow" "$(baslik "$ADRES/api/ortam")"
satir "index.html meta robots" "1" \
  "$(govde "$ADRES/" | grep -c 'name="robots"')"

# --- 5b. Onbellek -----------------------------------------------------------
# Bu iki satir bir DAGITIM kusurunu bekliyor, bir yapilandirma tercihini
# degil: index.html onbelleklenirse donen ziyaretci dagitimdan sonra ESKI
# uygulamayi acar ve bunu kimse fark etmez - site ayakta, kontroller yesil,
# yalnizca kullanicinin gordugu sey eskidir.
satir "index.html onbelleklenmiyor" "no-cache" \
  "$(curl -sS -D - -o /dev/null -m 20 "$ADRES/" \
     | sed -n 's/^[Cc]ache-[Cc]ontrol:[[:space:]]*//p' | tr -d '\r')"
# Olmayan bir paket 404 DONMELI. SPA geri dusumu onu index.html ile 200
# donduruyordu; eski bir index.html eski paketi istediginde hata ses
# cikarmiyor, uygulama sessizce bozuluyordu.
satir "eksik paket 404 doner" "404" \
  "$(kod "$ADRES/assets/olmayan-paket-kontrolu.js")"

# --- 6. Sunucu tarafi (yerelde kosuyorsa) -----------------------------------
if [ -d "$KURULUM" ]; then
  satir "sifirlama timer etkin" "enabled" \
    "$(systemctl is-enabled vardis-demo-sifirlama.timer 2>&1)"
  # TIMER ETKIN OLMASI SERVISIN BASARILI OLDUGU ANLAMINA GELMEZ. Sifirlama
  # kuruldugundan beri her gece `ExecStartPre`de dusuyordu ve disaridan
  # bakinca her sey saglam gorunuyordu: timer etkin, sonraki kosum yazili,
  # servisler ayakta. Eksik olan tam da bu satirdi.
  satir "son sifirlama sonucu" "success" \
    "$(systemctl show vardis-demo-sifirlama.service -p Result --value 2>&1)"
  echo "          sonraki kosum: $(systemctl list-timers vardis-demo-sifirlama.timer \
    --no-pager --no-legend 2>/dev/null | awk '{print $1, $2, $3}')"
  satir ".yasakli-metinler yerinde" "yes" \
    "$([ -s "$KURULUM/.yasakli-metinler" ] && echo yes || echo no)"
  satir "DEMO_PAROLA_TOHUMU tanimli" "yes" \
    "$(grep -q '^DEMO_PAROLA_TOHUMU=..*' "$KURULUM/.env" && echo yes || echo no)"
else
  echo "  [ATLANDI] sunucu tarafi ucu — $KURULUM burada yok"
fi

echo
echo "== gecti: $gecti · kaldi: $kaldi =="
[ "$kaldi" -eq 0 ]
