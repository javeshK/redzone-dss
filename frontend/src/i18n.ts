export type Lang = 'en' | 'hi';

const dict: Record<Lang, Record<string, string>> = {
  en: {
    'nav.overview': 'Overview',
    'nav.map': 'Risk Map',
    'nav.habitation': 'Habitation',
    'nav.planner': 'Relocation Planner',
    'priority.immediate': 'Immediate',
    'priority.shortterm': 'Short-term',
    'priority.mediumterm': 'Medium-term',
    'priority.monitor': 'Monitor',
    'disclaimer.derived': 'Derived scores are not official government hazard zonation.',
    'disclaimer.capacity': 'Capacity is first-order physical screening capacity, not statutory capacity.',
    'overview.lastUpdated': 'Last updated',
    'overview.refresh': 'Refresh data',
    'overview.alerts': 'Active Alerts',
    'map.scenario': 'Rainfall scenario',
    'map.scenarioBanner': 'Scenario mode — rainfall scaled for decision-support exploration only. Not a forecast.',
    'map.habitations': 'Habitations',
  },
  hi: {
    'nav.overview': 'अवलोकन',
    'nav.map': 'जोखिम मानचित्र',
    'nav.habitation': 'बस्ती',
    'nav.planner': 'पुनर्वास योजनाकार',
    'priority.immediate': 'तत्काल',
    'priority.shortterm': 'अल्पकालिक',
    'priority.mediumterm': 'मध्यम अवधि',
    'priority.monitor': 'निगरानी',
    'disclaimer.derived': 'व्युत्पन्न स्कोर आधिकारिक सरकारी खतरा ज़ोन नहीं हैं।',
    'disclaimer.capacity': 'क्षमता प्रथम-स्तरीय भौतिक स्क्रीनिंग क्षमता है, वैधानिक क्षमता नहीं।',
    'overview.lastUpdated': 'अंतिम अद्यतन',
    'overview.refresh': 'डेटा रीफ़्रेश करें',
    'overview.alerts': 'सक्रिय अलर्ट',
    'map.scenario': 'वर्षा परिदृश्य',
    'map.scenarioBanner': 'परिदृश्य मोड — निर्णय समर्थन के लिए वर्षा स्केल की गई। पूर्वानुमान नहीं।',
    'map.habitations': 'बस्तियाँ',
  },
};

let currentLang: Lang = 'en';

export function setLang(lang: Lang) {
  currentLang = lang;
}

export function getLang(): Lang {
  return currentLang;
}

export function t(key: string): string {
  return dict[currentLang][key] ?? dict.en[key] ?? key;
}

export function translatePriority(priority: string): string {
  const map: Record<string, string> = {
    Immediate: t('priority.immediate'),
    'Short-term': t('priority.shortterm'),
    'Medium-term': t('priority.mediumterm'),
    Monitor: t('priority.monitor'),
  };
  return map[priority] ?? priority;
}
