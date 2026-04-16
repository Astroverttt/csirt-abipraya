/**
 * NVD API wrapper — now calls the backend instead of NVD directly.
 *
 * No more CORS issues, rate limiting handled server-side.
 */
import api from './api'

/**
 * Fetch recent CVEs from NVD for a list of package keywords.
 * @param {string[]} keywords - Package names to search for
 * @param {number} daysBack - How many days back to search (default 7)
 * @returns {Promise<Array>} Array of CVE objects
 */
export async function fetchRecentCVEs(keywords, daysBack = 7) {
  try {
    const res = await api.post('/nvd/cves', {
      keywords,
      days_back: daysBack
    })
    return res.data
  } catch (err) {
    console.warn('NVD search failed:', err)
    return []
  }
}

export function clearNVDCache() {
  api.post('/nvd/clear-cache').catch(() => {})
}
