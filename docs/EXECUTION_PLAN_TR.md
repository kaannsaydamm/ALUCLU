# ALUCLU yürütme planı

Bu plan “dünyanın en iyi mimarisi” ifadesini tek bir sıralama iddiası olarak
değil, ölçülen kalite–gecikme–bellek–enerji Pareto cephesinde ilerleme hedefi
olarak ele alır.

## Aşama 0 — Çalışan doğruluk çekirdeği

**Durum: tamamlandı**

Teslim kapıları:

- Dört bellek yolu gerçek artımlı state ile çalışıyor.
- State çağrılar arasında taşınıyor ve açıkça detach edilebiliyor.
- Step, rastgele chunk ve tek-scan çıktıları test toleransında aynı.
- Gelecek suffix geçmiş çıktıyı değiştirmiyor.
- Epizodik payda yalnız exact `z` toplamından geliyor.
- Router sıfır sıcaklıkta ungated yolla exact aynı ve toplam payda kütlesini
  koruyor.
- QR + küçük-çekirdek SVD dense \(d\times d\) SVD oluşturmuyor.
- Exact surprise cache batch-bazlı, strict-priority ve sabit kapasiteli.
- Tarihsel Zoology ve özel diagnostic hedef hizalamaları birbirine
  karıştırılmıyor.
- Portable release kapısı derleme, test, iki eğitim smoke'u ve benchmark'ı
  tek komutta çalıştırıyor.

## Aşama 1 — Küçük ölçek bilimsel seçim

**Durum: altyapı hazır; eşit bütçeli çoklu-seed koşular bu CPU oturumunda
tamamlanmadı**

Karşılaştırmalar:

1. Full causal attention.
2. Sabit pencere attention.
3. Gated Delta Rule‑2 only.
4. Gated Delta Rule‑2 + local.
5. Gated Delta Rule‑2 + exact surprise cache.
6. Gated Delta Rule‑2 + episodic capsules.
7. Tam ALUCLU.

Her model aynı tokenizer, veri sırası, parametre sınıfı, optimizer, eğitim
tokenı ve seed setiyle ölçülür. Zorunlu çıktılar:

- validation NLL/perplexity,
- MQAR accuracy'nin mesafe ve kapasite oranına göre tam eğrisi,
- RULER/NoLiMa/HELMET kategori skorları,
- batch‑1 prefill ve decode,
- doygun state byte,
- parametre ve eğitim tokenı,
- ortalama değil seed dağılımı ve güven aralığı.

**Geçiş kapısı:** Tam ALUCLU, en az bir kalite–state–TPOT düzleminde
nondominated kalmalı. Hiçbir noktada kalmıyorsa daha basit kazanan yapı
seçilir; ek lane yalnız karmaşıklık olduğu için korunmaz.

## Aşama 2 — Kernel ve sistem yolu

**Durum: bu pakette yok; CUDA/H100 sınıfı donanım ve profiler gerekir**

Uygulama sırası ölçülen hotspot'a göre:

1. Gated Delta Rule‑2 chunkwise forward/backward.
2. Sliding-window attention için üretim kernel'i.
3. Exact-cache projection/read fusion.
4. Epizodik slot read ve mass-routing fusion.
5. Compression olaylarının ayrı stream veya asenkron çalışma uygunluğu.

Her optimize yol token-recurrent oracle ile:

- forward,
- state,
- input/parameter gradient,
- mixed-precision toleransı,
- variable-length ve carried-state

bakımından karşılaştırılır.

**Geçiş kapısı:** İki GPU mimarisinde profiler kaydı; tok/s, TTFT, p50/p95/p99
TPOT, peak byte, DRAM byte/token ve joule/token. Tek donanım varsa iddia yalnız
o donanımla sınırlandırılır.

## Aşama 3 — Ölçek

**Durum: Aşama 1 ve 2 kanıtlarına bağlı**

Ölçek sırası:

1. 100–200M parametre pilot.
2. Aynı protokolle 1B sınıfı.
3. Başarılıysa daha büyük model ve uzun-context curriculum.

Eğitim, önce cache/archive kapasitesinin altında; sonra live eviction,
archive merge ve birden fazla ring wrap görülecek biçimde ilerler. Modelin hiç
eğitim görmediği bir compression rejiminde yalnız test edilmesi kabul edilmez.

## Durdurma koşulları

Şunlardan biri gerçekleşirse karmaşıklık azaltılır:

- Exact cache aynı state bütçesinde recency veya reservoir seçimini geçmiyor.
- TensorSketch router, degree‑1 yönlendirmeye karşı kalite/maliyet kazanmıyor.
- Episodic archive hatası recall kazancını siliyor.
- Learned fusion sürekli tek branch'e çöküyor.
- Kernel profili FFT/SVD veya state trafiğinin Pareto kazancını tükettiğini
  gösteriyor.

Amaç bütün bileşenleri ne pahasına olursa olsun korumak değil; kanıtlanan en
küçük ALUCLU varyantını bulmaktır.
