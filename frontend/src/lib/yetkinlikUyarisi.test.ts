import { describe, expect, it } from 'vitest'
import { yetkinlikCakismaUyarisi } from './yetkinlikUyarisi'

describe('yetkinlikCakismaUyarisi', () => {
  it('Müracaat Görevlisi ile Güvenlik Görevi birlikteyse uyarır', () => {
    const uyari = yetkinlikCakismaUyarisi(['Müracaat Görevlisi', 'Güvenlik Görevi'])
    expect(uyari).not.toBeNull()
    // Uyarı DAYANAĞINI taşımalı: kullanıcı "neden" diye sorduğunda
    // bakacağı yeri metnin kendisi göstermeli.
    expect(uyari).toContain('3.3.2')
  })

  it('sıra önemsizdir', () => {
    expect(yetkinlikCakismaUyarisi(['Güvenlik Görevi', 'Müracaat Görevlisi'])).not.toBeNull()
  })

  it('tek başına hiçbiri uyarı üretmez', () => {
    expect(yetkinlikCakismaUyarisi(['Müracaat Görevlisi'])).toBeNull()
    expect(yetkinlikCakismaUyarisi(['Güvenlik Görevi'])).toBeNull()
    expect(yetkinlikCakismaUyarisi([])).toBeNull()
  })

  it('Vardiya Şefi + Güvenlik Görevi çifti uyarı DEĞİLDİR', () => {
    // SRS 3.3.2: vardiya şefi Güvenlik Görevi yetkinliğini zaten taşır.
    // Bu çifti uyarmak, doğru olan tek yapılandırmayı hatalı gösterirdi.
    expect(yetkinlikCakismaUyarisi(['Vardiya Şefi', 'Güvenlik Görevi'])).toBeNull()
  })
})
