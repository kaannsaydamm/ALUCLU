# ALUCLU adlandırma ve teknik kimlik

## Kanonik ad

- **Resmî ad:** ALUCLU
- **Açılım:** Adaptive Layered Unified Context with Learned Updates
- **Kod/paket adı:** `aluclu`
- **Tam teknik kullanım:** ALUCLU Memory Architecture
- **Tasarımcı:** Kaan Kadir Aluçlu
- **Kısa söz:** Bağlamı katmanla, belleği sınırla, hatırlamayı ölç.

Mimari adı bütün insan ve makine bağlamlarında ASCII `C` ile `ALUCLU`
olarak yazılır. Böylece ad, **Adaptive Layered Unified Context with Learned
Updates** açılımının baş harfleriyle birebir örtüşür. Python paketi, dosya
yolları ve protokol kimliklerinde küçük harfli `aluclu` kullanılır. Tasarımcının
soyadı kişi ve atıf alanlarında özgün biçimiyle `Aluçlu` kalır.

## İlk kullanım

Bir belgede ilk kullanım:

> ALUCLU (Adaptive Layered Unified Context with Learned Updates), Kaan Kadir
> Aluçlu tarafından tasarlanan sınırlı-durumlu hibrit bir bellek mimarisidir.

Sonraki kullanımlarda yalnız `ALUCLU` yeterlidir.

## Mesaj omurgası

Birincil mesaj:

> ALUCLU, farklı fiziksel bellek rejimlerini tek bir öğrenilebilir blokta
> birleştirir ve her kapasite–hız–hatırlama ödünleşimini ölçülebilir bırakır.

Kanıt sırası:

1. Matematiksel invariant ve fiziksel sınır.
2. Tekrarlanabilir test veya benchmark.
3. Donanım ve protokol bilgisi.
4. Yalnız ölçümün desteklediği kapsamda sonuç.

`En hızlı`, `en güçlü`, `kayıpsız` veya `sınırsız` gibi evrensel üstünlük
ifadeleri, bunları destekleyen açık ve eşit koşullu bir ölçüm olmadan marka
dilinde kullanılmaz.

## Bileşen adları

| İnsan tarafından okunan ad | Kod adı | Rol |
|---|---|---|
| ALUCLU block | `AlucluBlock` | Dört bellek yolunu birleştiren blok |
| learned-update memory | `GatedDeltaRule2` | Sabit boyutlu yoğun recurrent bellek |
| exact local memory | `BoundedLocalAttention` | Son pencere üzerinde tam softmax |
| exact surprise memory | `ResidualSurpriseCache` | Yüksek yazma artıklı seyrek tam KV |
| episodic capsule memory | `BoundedEpisodicMemory` | Exact yakın segmentler ve düşük-rank arşiv |
| mass-conserving routing | `MassConservingRouter` | Payda kütlesini koruyan kapsül yönlendirme |

## Şema renkleri

Renkler yalnız anlatımı kolaylaştırır; mimari semantiğin yerine geçmez.

| Token | Hex | Kullanım |
|---|---|---|
| Graphite | `#111827` | Metin ve ana omurga |
| Copper | `#B45309` | ALUCLU marka vurgusu |
| Cyan | `#0891B2` | Learned-update yolu |
| Emerald | `#047857` | Exact local/surprise yolları |
| Violet | `#6D28D9` | Episodic capsule yolu |
| Slate | `#64748B` | Ölçüm, sınır ve uyarılar |

## Atıf

Yazılım veya deney çıktısında önerilen kısa atıf:

> ALUCLU Memory Architecture, Kaan Kadir Aluçlu, 2026.

Bu adlandırma belgesi teknik yazarlık bilgisidir; marka tescili veya hukuki
çakışma görüşü değildir.
