import {
  HabitationDetail,
  HabitationSummary,
  PriorityClass,
  RecommendationResponse,
  SiteRecommendation,
  ZoneClass,
} from '../types';
import { t } from '../i18n';

function hazardLevel(h: number): 'high' | 'moderate' | 'low' {
  if (h >= 0.7) return 'high';
  if (h >= 0.4) return 'moderate';
  return 'low';
}

function accessLabel(score: number): string {
  if (score >= 0.8) return t('access.good');
  if (score >= 0.6) return t('access.fair');
  return t('access.poor');
}

/** One-sentence risk summary for a village. */
export function getRiskSummary(hab: HabitationSummary): string {
  const level = hazardLevel(hab.h);
  const zone = hab.zone_class.toLowerCase();
  if (hab.pct_red >= 40) {
    return t('summary.risk.highRedPct').replace('{pct}', hab.pct_red.toFixed(0)).replace('{zone}', zone);
  }
  if (level === 'high') {
    return t('summary.risk.high').replace('{zone}', zone);
  }
  if (level === 'moderate') {
    return t('summary.risk.moderate').replace('{zone}', zone);
  }
  return t('summary.risk.low').replace('{zone}', zone);
}

/** Plain-language reasons why relocation / rehabilitation may be needed. */
export function getRehabilitationReasons(hab: HabitationDetail): string[] {
  const reasons: string[] = [];

  if (hab.pct_red >= 40) {
    reasons.push(t('reason.pctRed').replace('{pct}', hab.pct_red.toFixed(0)));
  }
  if (hab.h_ff >= 0.65) {
    reasons.push(t('reason.flashFlood'));
  }
  if (hab.h_ls >= 0.55) {
    reasons.push(t('reason.landslide'));
  }
  if (hab.h >= 0.75) {
    reasons.push(t('reason.overallHazard'));
  }

  const histExposure = hab.vuln_explain.find((e) => e.factor === 'historical_exposure');
  if (histExposure && histExposure.value >= 0.7) {
    reasons.push(t('reason.historical'));
  }
  const popFactor = hab.vuln_explain.find((e) => e.factor === 'population');
  if (popFactor && popFactor.value >= 0.6) {
    reasons.push(t('reason.largePop').replace('{pop}', String(hab.pop)));
  }
  const healthFactor = hab.vuln_explain.find((e) => e.factor === 'health_access');
  if (healthFactor && healthFactor.value >= 0.5) {
    reasons.push(t('reason.healthGap'));
  }

  const override = hab.explain.find(
    (e) => e.factor === 'pct_red_override' || e.factor === 'h_hab_override',
  );
  if (override?.note) {
    reasons.push(override.note.replace('forces Immediate', t('reason.forcesImmediate')));
  }

  if (reasons.length === 0) {
    reasons.push(t('reason.default'));
  }

  return reasons;
}

/** What the user should do next, based on priority. */
export function getActionSteps(
  hab: HabitationSummary,
  hasRelocation: boolean,
): { step: number; text: string; urgent?: boolean }[] {
  const steps: { step: number; text: string; urgent?: boolean }[] = [];

  if (hab.priority === 'Immediate') {
    steps.push({ step: 1, text: t('action.immediate.1'), urgent: true });
    steps.push({ step: 2, text: t('action.immediate.2'), urgent: true });
    if (hasRelocation) {
      steps.push({ step: 3, text: t('action.immediate.3') });
    }
    steps.push({ step: steps.length + 1, text: t('action.immediate.4') });
  } else if (hab.priority === 'Short-term') {
    steps.push({ step: 1, text: t('action.short.1') });
    steps.push({ step: 2, text: t('action.short.2') });
    if (hasRelocation) steps.push({ step: 3, text: t('action.short.3') });
  } else if (hab.priority === 'Medium-term') {
    steps.push({ step: 1, text: t('action.medium.1') });
    steps.push({ step: 2, text: t('action.medium.2') });
  } else {
    steps.push({ step: 1, text: t('action.monitor.1') });
    steps.push({ step: 2, text: t('action.monitor.2') });
  }

  return steps;
}

/** Short subtitle for habitation list rows. */
export function getHabitationListSubtitle(hab: HabitationSummary, siteName?: string): string {
  const parts = [
    `${hab.block}`,
    `${hab.pop} ${t('label.people')}`,
    `${hab.pct_red.toFixed(0)}% ${t('label.inDangerZone')}`,
  ];
  if (siteName) {
    parts.push(`→ ${siteName}`);
  }
  return parts.join(' · ');
}

/** Convert backend reason strings to plainer language. */
export function simplifyReason(reason: string): string {
  if (reason.includes('H_site=') && reason.includes('below')) {
    return t('reason.siteSafer');
  }
  if (reason.includes('H_site=') || reason.includes('U_ij')) {
    return '';
  }
  if (reason.startsWith('Access:')) {
    const road = reason.match(/road ([\d.]+)/);
    const health = reason.match(/healthcare ([\d.]+)/);
    const water = reason.match(/water ([\d.]+)/);
    const school = reason.match(/school ([\d.]+)/);
    const parts: string[] = [];
    if (road) parts.push(`${t('label.roads')}: ${accessLabel(parseFloat(road[1]))}`);
    if (health) parts.push(`${t('label.healthcare')}: ${accessLabel(parseFloat(health[1]))}`);
    if (water) parts.push(`${t('label.water')}: ${accessLabel(parseFloat(water[1]))}`);
    if (school) parts.push(`${t('label.schools')}: ${accessLabel(parseFloat(school[1]))}`);
    return parts.join(' · ');
  }
  if (reason.includes('Distance') && reason.includes('km from')) {
    const m = reason.match(/Distance ([\d.]+) km from (.+?) \(/);
    if (m) return t('reason.distance').replace('{km}', m[1]).replace('{name}', m[2]);
    return reason.split('(')[0].trim();
  }
  if (reason.includes('screening capacity')) {
    const m = reason.match(/capacity: (\d+) available \(habitation pop (\d+)\)/i);
    if (m) {
      return t('reason.capacity')
        .replace('{avail}', m[1])
        .replace('{pop}', m[2]);
    }
  }
  if (reason.includes('split relocation')) {
    return t('reason.splitRelocation');
  }
  if (reason.includes('meets') && reason.includes('threshold')) {
    return t('reason.capacityOk');
  }
  if (reason.includes('U_ij=') || reason.includes('Δ')) {
    return '';
  }
  return reason;
}

export function getPlainSiteReasons(site: SiteRecommendation): string[] {
  return site.reasons.map(simplifyReason).filter(Boolean);
}

export function getRelocationHeadline(rec: RecommendationResponse): string {
  return t('reloc.headline')
    .replace('{hab}', rec.hab_name)
    .replace('{site}', rec.top.site_name);
}

export function getZonePlainLabel(zone: ZoneClass): string {
  const map: Record<ZoneClass, string> = {
    Red: t('zone.red'),
    Orange: t('zone.orange'),
    Yellow: t('zone.yellow'),
    Green: t('zone.green'),
  };
  return map[zone];
}

export function getPriorityPlainLabel(priority: PriorityClass): string {
  const map: Record<PriorityClass, string> = {
    Immediate: t('priority.immediate'),
    'Short-term': t('priority.shortterm'),
    'Medium-term': t('priority.mediumterm'),
    Monitor: t('priority.monitor'),
  };
  return map[priority];
}

export function simplifyAlertReason(reason: string): string {
  if (reason.includes('H_ff=') && reason.includes('exceeds')) {
    return t('alert.flashFloodHigh');
  }
  if (reason.includes('H_hab=') || reason.includes('hazard')) {
    return t('alert.hazardHigh');
  }
  if (reason.includes('pct_red') || reason.includes('%')) {
    return t('alert.redZoneHigh');
  }
  if (reason.includes('Immediate')) {
    return t('alert.needsRelocation');
  }
  if (reason.includes('buffer')) {
    return t('alert.nearStream');
  }
  return simplifyReason(reason) || reason;
}
