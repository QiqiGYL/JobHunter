import { useState, useEffect, useCallback, useRef } from 'react'
import { Drawer, Progress, Tag, Table } from 'antd'
import { JobList } from './JobList'
import { ResumeUpload } from './ResumeUpload'
import './App.css'

const API = '/api'
const PAGE_SIZE = 10

const LANGS = {
  en: {
    subtitle: 'Job matching in the last 24h · ranked by resume match score',
    loading: 'Loading…',
    retry: 'Retry',
    tabJobs: 'Matched Jobs',
    tabFiltered: 'Filtered Out',
    drawerTitle: 'ATS Analysis',
    missingKeywords: 'Missing Keywords (Gap Analysis)',
    resumeSurgery: 'Resume Surgery',
    noStructured: 'No structured result — raw response:',
    colOriginal: 'Original',
    colOptimized: 'Optimized',
    requestFailed: 'Request failed',
    noApiKey: 'ATS Analysis requires a DeepSeek API key. Add DEEPSEEK_API_KEY to your .env file and restart the backend.',
    emptyListIntro: 'No data found. Run ',
    emptyListOutro: ' first to scrape jobs and fill the database. Then set filters and click Run to update the list.',
    prevPage: 'Prev',
    nextPage: 'Next',
    viewJob: 'View Job',
    rejectionReason: 'Filtered:',
    filterLabel: 'Filters',
    yearsExp: 'Years of experience',
    yearsMin: 'Min',
    yearsMax: 'Max',
    graduationYear: 'Graduation year',
    graduationYearPlaceholder: 'Any (new grad & non-new grad)',
    jobType: 'Job type',
    jobTypeSoftware: 'Software Developer',
    jobTypeQA: 'Quality Assurance',
    jobTypeData: 'Data Analyst',
    jobTypeAny: 'Any',
    excludeInternCoop: 'Exclude Intern / CO-OP',
    resetFilters: 'Reset',
    runFilters: 'Run',
    refreshJobsFirst: 'Refresh jobs from web first (then apply filters)',
    refreshingJobs: 'Refreshing jobs from web…',
    filterHint: 'Upload resume (optional) → set filters → click Run to update the list.',
    locationCountry: 'Location',
    locationAny: 'Any',
    locationCanada: 'Canada',
    locationUS: 'United States',
    tabApplied: (n) => `Applied (${n})`,
    markApplied: 'Mark as applied',
    appliedLabel: 'Applied',
    lastScrape: 'Last scrape',
    afterDedup: 'after dedup',
    removed: 'removed',
    scrapeStatsHint: 'No scrape stats yet. Check "Refresh jobs from web first" and click Run to see LinkedIn/Indeed counts.',
  },
  zh: {
    subtitle: '过去 24 小时职位匹配 · 按简历契合度排名',
    loading: '加载中…',
    retry: '重试',
    tabJobs: '保留的职位',
    tabFiltered: '已筛除',
    drawerTitle: 'ATS 分析',
    missingKeywords: '缺失关键词 (Gap Analysis)',
    resumeSurgery: '简历手术 (Resume Surgery)',
    noStructured: '无结构化结果，原始回复：',
    colOriginal: '原描述',
    colOptimized: '优化后',
    requestFailed: '请求失败',
    noApiKey: 'ATS 分析需要 DeepSeek API Key。请在 .env 文件中设置 DEEPSEEK_API_KEY 后重启后端。',
    emptyListIntro: '暂无数据。请先运行 ',
    emptyListOutro: ' 抓取职位并写入数据库。之后设置筛选条件并点击「运行」更新列表。',
    prevPage: '上一页',
    nextPage: '下一页',
    viewJob: '查看职位',
    rejectionReason: '筛除原因:',
    filterLabel: '筛选',
    yearsExp: '工作年限',
    yearsMin: '最少',
    yearsMax: '最多',
    graduationYear: '毕业年份',
    graduationYearPlaceholder: '选填，不填则 new grad 与非 new grad 都显示',
    jobType: '职位类型',
    jobTypeSoftware: '软件开发',
    jobTypeQA: '质量保证 / QA',
    jobTypeData: '数据分析',
    jobTypeAny: '不限',
    excludeInternCoop: '排除实习 / CO-OP',
    resetFilters: '恢复默认',
    runFilters: '运行',
    refreshJobsFirst: '先从网页抓取职位再筛选',
    refreshingJobs: '正在抓取职位…',
    filterHint: '上传简历（可选）→ 填筛选条件 → 点击「运行」更新列表。',
    locationCountry: '地区',
    locationAny: '不限',
    locationCanada: '加拿大',
    locationUS: '美国',
    tabApplied: (n) => `已投递 (${n})`,
    markApplied: '标记为已投递',
    appliedLabel: '已投递',
    lastScrape: '上次抓取',
    afterDedup: '去重后',
    removed: '条已去重',
    scrapeStatsHint: '暂无抓取统计。勾选「先从网页抓取职位再筛选」并点击「运行」后可显示 LinkedIn/Indeed 各抓取条数。',
  },
}

export default function App() {
  const [lang, setLang] = useState('en')
  const t = LANGS[lang]
  const [jobs, setJobs] = useState([])
  const [filteredOut, setFilteredOut] = useState([])
  const [appliedJobs, setAppliedJobs] = useState([])
  const [appliedCount, setAppliedCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [resumeUploaded, setResumeUploaded] = useState(false)
  const [activeTab, setActiveTab] = useState('jobs')
  const [page, setPage] = useState(1)
  const [analysisByKey, setAnalysisByKey] = useState({})
  const [analysisLoadingKey, setAnalysisLoadingKey] = useState(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerJob, setDrawerJob] = useState(null)
  const [drawerData, setDrawerData] = useState(null)

  const [yearsMin, setYearsMin] = useState(0)
  const [yearsMax, setYearsMax] = useState(2)
  const [graduationYear, setGraduationYear] = useState('') // '' = any (optional)
  const [jobRoles, setJobRoles] = useState([])
  const [locationCountry, setLocationCountry] = useState('')
  const [excludeInternCoop, setExcludeInternCoop] = useState(true)
  const [filterBarOpen, setFilterBarOpen] = useState(true)
  const [jobTypeDropdownOpen, setJobTypeDropdownOpen] = useState(false)
  const [refreshJobsFirst, setRefreshJobsFirst] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [scrapeStats, setScrapeStats] = useState(null)

  const JOB_TYPE_OPTIONS = [
    { value: 'software_developer', labelKey: 'jobTypeSoftware' },
    { value: 'quality_assurance', labelKey: 'jobTypeQA' },
    { value: 'data_analyst', labelKey: 'jobTypeData' },
  ]
  const toggleJobRole = (role) => {
    setJobRoles((prev) => (prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]))
  }
  const jobTypeLabel = jobRoles.length === 0
    ? t.jobTypeAny
    : jobRoles.length === 1
      ? t[JOB_TYPE_OPTIONS.find((o) => o.value === jobRoles[0])?.labelKey || 'jobTypeAny']
      : `${jobRoles.length} selected`

  const fetchJobs = useCallback(async (tab = null) => {
    setLoading(true)
    setError(null)
    try {
      const wantApplied = tab === 'applied'
      const params = new URLSearchParams()
      if (wantApplied) {
        params.set('tab', 'applied')
      } else {
        params.set('years_min', String(yearsMin))
        params.set('years_max', String(yearsMax))
        params.set('exclude_intern_coop', excludeInternCoop ? 'true' : 'false')
        if (graduationYear !== '' && graduationYear != null) params.set('graduation_year', String(graduationYear))
        if (jobRoles.length > 0) params.set('job_roles', jobRoles.join(','))
        if (locationCountry) params.set('location_country', locationCountry)
      }
      const res = await fetch(`${API}/jobs?${params}`)
      if (!res.ok) throw new Error(res.statusText)
      const data = await res.json()
      setScrapeStats(data.scrapeStats ?? null)
      if (wantApplied) {
        setAppliedJobs(data.jobs || [])
        setAppliedCount((data.jobs || []).length)
      } else {
        setJobs(data.jobs || [])
        setFilteredOut(data.filteredOut || [])
        setAppliedCount(data.appliedCount != null ? data.appliedCount : 0)
      }
    } catch (e) {
      setError(e.message || 'Failed to load jobs')
      if (tab !== 'applied') {
        setJobs([])
        setFilteredOut([])
      } else setAppliedJobs([])
    } finally {
      setLoading(false)
    }
  }, [yearsMin, yearsMax, graduationYear, excludeInternCoop, jobRoles, locationCountry])

  const fetchJobsRef = useRef(fetchJobs)
  fetchJobsRef.current = fetchJobs
  const isFirstFetch = useRef(true)
  const FILTER_DEBOUNCE_MS = 400
  useEffect(() => {
    const delay = isFirstFetch.current ? 0 : FILTER_DEBOUNCE_MS
    isFirstFetch.current = false
    const t = setTimeout(() => fetchJobsRef.current(), delay)
    return () => clearTimeout(t)
  }, [yearsMin, yearsMax, graduationYear, excludeInternCoop, jobRoles, locationCountry])

  const handleResetFilters = () => {
    setYearsMin(0)
    setYearsMax(2)
    setGraduationYear('')
    setJobRoles([])
    setLocationCountry('')
    setExcludeInternCoop(true)
  }

  const handleResumeUploaded = async () => {
    setResumeUploaded(true)
    try {
      const res = await fetch(`${API}/resume/filter-suggestions`)
      if (res.ok) {
        const data = await res.json()
        if (data.graduation_year != null) setGraduationYear(Number(data.graduation_year))
        else setGraduationYear('')
        if (data.years_min != null) setYearsMin(Number(data.years_min))
        if (data.years_max != null) setYearsMax(Number(data.years_max))
      }
    } catch (_) {
      // ignore; keep current filter values
    }
  }

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    setPage(1)
    if (tab === 'applied') fetchJobs('applied')
  }

  const REFRESH_TIMEOUT_MS = 5 * 60 * 1000 // 5 min
  const handleRunFilters = useCallback(async () => {
    if (refreshing) return
    if (refreshJobsFirst) {
      setRefreshing(true)
      setError(null)
      try {
        const ac = new AbortController()
        const to = setTimeout(() => ac.abort(), REFRESH_TIMEOUT_MS)
        const res = await fetch(`${API}/jobs/refresh`, { method: 'POST', signal: ac.signal })
        clearTimeout(to)
        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          const detail = data.detail ? `\n${String(data.detail).trim().slice(0, 1500)}` : ''
          throw new Error((data.error || res.statusText) + detail)
        }
      } catch (e) {
        setRefreshing(false)
        setError(e.name === 'AbortError' ? 'Refresh timed out' : (e.message || 'Refresh failed'))
        return
      }
      setRefreshing(false)
    }
    fetchJobs()
  }, [refreshing, refreshJobsFirst, fetchJobs])

  const handleRequestAnalysis = async (job, jobKey) => {
    const cached = analysisByKey[jobKey]
    if (cached) {
      setDrawerJob(job)
      setDrawerData(cached)
      setDrawerOpen(true)
      return
    }
    setAnalysisLoadingKey(jobKey)
    try {
      const res = await fetch(`${API}/jobs/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job: {
            title: job.title,
            company: job.company,
            description: job.description,
            job_url: job.job_url,
          },
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (res.status === 403 && data.error === 'no_api_key') {
        setDrawerData({ analysis: null, raw: t.noApiKey })
      } else if (!res.ok) {
        setDrawerData({ analysis: null, raw: data.error || res.statusText })
      } else {
        setAnalysisByKey((prev) => ({ ...prev, [jobKey]: { analysis: data.analysis, raw: data.raw } }))
        setDrawerData({ analysis: data.analysis, raw: data.raw })
      }
      setDrawerJob(job)
      setDrawerOpen(true)
    } catch (e) {
      setDrawerData({ analysis: null, raw: e.message || t.requestFailed })
      setDrawerJob(job)
      setDrawerOpen(true)
    } finally {
      setAnalysisLoadingKey(null)
    }
  }

  const currentItems =
    activeTab === 'jobs' ? jobs
    : activeTab === 'applied' ? appliedJobs
    : filteredOut
  const totalPages = Math.max(1, Math.ceil(currentItems.length / PAGE_SIZE))
  const paginatedItems = currentItems.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleMarkApplied = useCallback(() => {
    fetchJobs()
    if (activeTab === 'applied') fetchJobs('applied')
  }, [fetchJobs, activeTab])

  return (
    <div className="app">
      <div className="lang-switcher">
        <button
          type="button"
          className={`lang-seg ${lang === 'en' ? 'lang-seg-active' : ''}`}
          onClick={() => setLang('en')}
        >EN</button>
        <button
          type="button"
          className={`lang-seg ${lang === 'zh' ? 'lang-seg-active' : ''}`}
          onClick={() => setLang('zh')}
        >CN</button>
      </div>

      <header className="header">
        <div className="header-hero">
          <h1 className="header-title">JobHunter</h1>
          <p className="subtitle">{t.subtitle}</p>
        </div>
        <div className="header-resume">
          <ResumeUpload onUploaded={handleResumeUploaded} lang={lang} />
        </div>
      </header>

      {(loading || refreshing) && (
        <div className="loading">{refreshing ? t.refreshingJobs : t.loading}</div>
      )}
      {error && (
        <div className="error">
          <span className="error-message">{error}</span>
          <button type="button" onClick={fetchJobs}>{t.retry}</button>
        </div>
      )}

      {!loading && !refreshing && !error && (
        <section className="section">
          <div className="tabs">
            <button
              type="button"
              className={activeTab === 'jobs' ? 'active' : ''}
              onClick={() => handleTabChange('jobs')}
            >
              {t.tabJobs}
            </button>
            <button
              type="button"
              className={activeTab === 'filteredOut' ? 'active' : ''}
              onClick={() => handleTabChange('filteredOut')}
            >
              {t.tabFiltered}
            </button>
            <button
              type="button"
              className={activeTab === 'applied' ? 'active' : ''}
              onClick={() => handleTabChange('applied')}
            >
              {t.tabApplied(appliedCount)}
            </button>
          </div>
          <div className="filter-bar-wrap">
            <button
              type="button"
              className="filter-bar-toggle"
              onClick={() => setFilterBarOpen((o) => !o)}
              aria-expanded={filterBarOpen}
            >
              {t.filterLabel} {filterBarOpen ? '▼' : '▶'}
            </button>
            {filterBarOpen && (
              <div className="filter-bar">
                <span className="filter-bar-label">{t.yearsExp}</span>
                <input
                  type="number"
                  min={0}
                  max={20}
                  value={yearsMin}
                  onChange={(e) => {
                    const v = Number(e.target.value) || 0
                    setYearsMin(v)
                    if (v > yearsMax) setYearsMax(v)
                  }}
                  className="filter-input filter-input-num"
                  aria-label={t.yearsMin}
                />
                <span className="filter-bar-sep">–</span>
                <input
                  type="number"
                  min={0}
                  max={20}
                  value={yearsMax}
                  onChange={(e) => {
                    const v = Number(e.target.value) || 0
                    setYearsMax(v)
                    if (v < yearsMin) setYearsMin(v)
                  }}
                  className="filter-input filter-input-num"
                  aria-label={t.yearsMax}
                />
                <span className="filter-bar-label">{t.graduationYear}</span>
                <input
                  type="number"
                  min={2020}
                  max={2030}
                  value={graduationYear === '' ? '' : graduationYear}
                  onChange={(e) => setGraduationYear(e.target.value === '' ? '' : (Number(e.target.value) || ''))}
                  placeholder={t.graduationYearPlaceholder}
                  className="filter-input filter-input-num"
                  title={t.graduationYearPlaceholder}
                />
                <span className="filter-bar-label">{t.jobType}</span>
                <div className="filter-multiselect-wrap">
                  <button
                    type="button"
                    className="filter-input filter-select filter-multiselect-trigger"
                    onClick={() => setJobTypeDropdownOpen((o) => !o)}
                    aria-expanded={jobTypeDropdownOpen}
                    aria-haspopup="listbox"
                  >
                    {jobTypeLabel}
                    <span className="filter-multiselect-arrow">{jobTypeDropdownOpen ? '▲' : '▼'}</span>
                  </button>
                  {jobTypeDropdownOpen && (
                    <div
                      className="filter-multiselect-dropdown"
                      role="listbox"
                      aria-multiselectable="true"
                    >
                      {JOB_TYPE_OPTIONS.map((opt) => (
                        <label
                          key={opt.value}
                          className="filter-multiselect-option"
                          role="option"
                          aria-selected={jobRoles.includes(opt.value)}
                        >
                          <input
                            type="checkbox"
                            checked={jobRoles.includes(opt.value)}
                            onChange={() => toggleJobRole(opt.value)}
                          />
                          {t[opt.labelKey]}
                        </label>
                      ))}
                    </div>
                  )}
                </div>
                {jobTypeDropdownOpen && (
                  <div
                    className="filter-multiselect-backdrop"
                    role="presentation"
                    onClick={() => setJobTypeDropdownOpen(false)}
                    aria-hidden="true"
                  />
                )}
                <span className="filter-bar-label">{t.locationCountry}</span>
                <select
                  value={locationCountry}
                  onChange={(e) => setLocationCountry(e.target.value)}
                  className="filter-input filter-select"
                  aria-label={t.locationCountry}
                >
                  <option value="">{t.locationAny}</option>
                  <option value="Canada">{t.locationCanada}</option>
                  <option value="United States">{t.locationUS}</option>
                </select>
                <label className="filter-bar-check">
                  <input
                    type="checkbox"
                    checked={excludeInternCoop}
                    onChange={(e) => setExcludeInternCoop(e.target.checked)}
                  />
                  {t.excludeInternCoop}
                </label>
                <label className="filter-bar-check">
                  <input
                    type="checkbox"
                    checked={refreshJobsFirst}
                    onChange={(e) => setRefreshJobsFirst(e.target.checked)}
                  />
                  {t.refreshJobsFirst}
                </label>
                <p className="filter-hint">{t.filterHint}</p>
                <span className="filter-actions">
                  <button type="button" className="filter-reset-btn" onClick={handleResetFilters}>
                    {t.resetFilters}
                  </button>
                  <span className="filter-actions-sep">|</span>
                  <button
                    type="button"
                    className="filter-run-btn"
                    onClick={handleRunFilters}
                    disabled={refreshing}
                  >
                    {refreshing ? t.refreshingJobs : t.runFilters}
                  </button>
                </span>
              </div>
            )}
          </div>
          <p className="scrape-stats">
            {scrapeStats && (scrapeStats.total_scraped != null || (scrapeStats.by_site && Object.keys(scrapeStats.by_site).length > 0)) ? (
              <>
                {t.lastScrape}:{' '}
                {scrapeStats.by_site && Object.keys(scrapeStats.by_site).length > 0 ? (
                  <>
                    {Object.entries(scrapeStats.by_site)
                      .map(([site, o]) => `${site.charAt(0).toUpperCase() + site.slice(1)} ${o.got}/${o.requested}`)
                      .join(', ')}
                    ;{' '}
                  </>
                ) : null}
                {scrapeStats.total_scraped != null && (
                  <>{scrapeStats.total_scraped} total → {scrapeStats.total_after_dedup} {t.afterDedup} ({scrapeStats.dedup_removed} {t.removed})</>
                )}
              </>
            ) : (
              <span className="scrape-stats-hint">{t.scrapeStatsHint}</span>
            )}
          </p>
          <JobList
            items={paginatedItems}
            isFilteredOut={activeTab === 'filteredOut'}
            isAppliedTab={activeTab === 'applied'}
            totalCount={currentItems.length}
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
            activeTab={activeTab}
            baseIndex={(page - 1) * PAGE_SIZE}
            onRequestAnalysis={handleRequestAnalysis}
            analysisLoadingKey={analysisLoadingKey}
            onMarkApplied={handleMarkApplied}
            t={t}
          />
        </section>
      )}

      <Drawer
        title={drawerJob ? `${drawerJob.title} @ ${drawerJob.company}` : t.drawerTitle}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={560}
        destroyOnClose={false}
      >
        {drawerData && (
          <AnalysisDrawerContent data={drawerData} t={t} />
        )}
      </Drawer>
    </div>
  )
}

function AnalysisDrawerContent({ data, t }) {
  const { analysis, raw } = data
  if (analysis) {
    const score = analysis.ats_match_score != null ? Number(analysis.ats_match_score) : null
    const keywords = analysis.missing_keywords || []
    const edits = analysis.resume_edits || []
    const editColumns = [
      { title: t.colOriginal, dataIndex: 'original', key: 'original', width: '45%' },
      { title: t.colOptimized, dataIndex: 'optimized', key: 'optimized', width: '55%', render: (v) => <span className="resume-edit-optimized">{v}</span> },
    ]
    return (
      <div className="analysis-drawer">
        {score != null && (
          <div className="analysis-score">
            <Progress type="circle" percent={score} size={120} strokeColor="#0a7c42" />
            <span className="analysis-score-label">ATS Match Score</span>
          </div>
        )}
        {keywords.length > 0 && (
          <div className="analysis-section">
            <h4>{t.missingKeywords}</h4>
            <div className="analysis-tags">
              {keywords.map((k, i) => (
                <Tag key={i} color="red">{k}</Tag>
              ))}
            </div>
          </div>
        )}
        {edits.length > 0 && (
          <div className="analysis-section">
            <h4>{t.resumeSurgery}</h4>
            <Table dataSource={edits.map((e, i) => ({ ...e, key: i }))} columns={editColumns} pagination={false} size="small" />
          </div>
        )}
        {analysis.ats_red_flags && (
          <div className="analysis-section">
            <h4>ATS Red Flags</h4>
            <p className="analysis-text">{analysis.ats_red_flags}</p>
          </div>
        )}
        {analysis.interview_prediction && (
          <div className="analysis-section">
            <h4>Interview Prediction</h4>
            <p className="analysis-text">{analysis.interview_prediction}</p>
          </div>
        )}
      </div>
    )
  }
  return (
    <div className="analysis-drawer">
      <p className="analysis-raw">{t.noStructured}</p>
      <pre className="analysis-raw-pre">{raw || '—'}</pre>
    </div>
  )
}
