const API_BASE_URL = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed with status: ${res.status}`);
  }
  return res.json();
}

export async function fetchAvailableDates() {
  const res = await fetch(`${API_BASE_URL}/dates`);
  if (!res.ok) {
    throw new Error(`Failed to fetch January 2026 dates: ${res.status}`);
  }
  return res.json();
}

export async function fetchAnalysis({
  deliveryDate,
  cutoffHour = 11,
  cutoffDayOffset = 1,
  alignmentMode = 'half_hourly_expanded',
  forceFixture = false
}) {
  const params = new URLSearchParams({
    delivery_date: deliveryDate,
    cutoff_hour: cutoffHour.toString(),
    cutoff_day_offset: cutoffDayOffset.toString(),
    alignment_mode: alignmentMode
  });
  if (forceFixture) {
    params.append('force_fixture', 'true');
  }

  const res = await fetch(`${API_BASE_URL}/analysis?${params.toString()}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Analysis request failed with status: ${res.status}`);
  }
  return res.json();
}

export async function fetchVintageComparison({
  deliveryDate,
  cutoffHour = 11,
  cutoffDayOffset = 1,
  forceFixture = false
}) {
  const params = new URLSearchParams({
    delivery_date: deliveryDate,
    cutoff_hour: cutoffHour.toString(),
    cutoff_day_offset: cutoffDayOffset.toString()
  });
  if (forceFixture) {
    params.append('force_fixture', 'true');
  }

  const res = await fetch(`${API_BASE_URL}/vintages/compare?${params.toString()}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Vintage comparison failed with status: ${res.status}`);
  }
  return res.json();
}
