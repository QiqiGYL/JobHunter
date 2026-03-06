import { useState, useEffect } from 'react'
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
    emptyList: (cmd) => `No data found. Run ${cmd} first to generate job_hunt_results.xlsx.`,
    prevPage: 'Prev',
    nextPage: 'Next',
    viewJob: 'View Job',
    rejectionReason: 'Filtered:',
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
    emptyList: (cmd) => `暂无数据。请先运行 ${cmd} 生成 job_hunt_results.xlsx。`,
    prevPage: '上一页',
    nextPage: '下一页',
    viewJob: '查看职位',
    rejectionReason: '筛除原因:',
  },
}

export const LangContext = { current: 'en' }

export default function App() {
  const [lang, setLang] = useState('en')
  const t = LANGS[lang]
  const [jobs, setJobs] = useState([])
  const [filteredOut, setFilteredOut] = useState([])
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

  const fetchJobs = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API}/jobs`)
      if (!res.ok) throw new Error(res.statusText)
      const data = await res.json()
      setJobs(data.jobs || [])
      setFilteredOut(data.filteredOut || [])
    } catch (e) {
      setError(e.message || 'Failed to load jobs')
      setJobs([])
      setFilteredOut([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs()
  }, [])

  const handleResumeUploaded = () => {
    setResumeUploaded(true)
  }

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    setPage(1)
  }

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

  const currentItems = activeTab === 'jobs' ? jobs : filteredOut
  const totalPages = Math.max(1, Math.ceil(currentItems.length / PAGE_SIZE))
  const paginatedItems = currentItems.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

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
          <ResumeUpload onUploaded={handleResumeUploaded} />
        </div>
      </header>

      {loading && <div className="loading">{t.loading}</div>}
      {error && (
        <div className="error">
          {error}
          <button type="button" onClick={fetchJobs}>{t.retry}</button>
        </div>
      )}

      {!loading && !error && (
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
          </div>
          <JobList
            items={paginatedItems}
            isFilteredOut={activeTab === 'filteredOut'}
            totalCount={currentItems.length}
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
            activeTab={activeTab}
            baseIndex={(page - 1) * PAGE_SIZE}
            onRequestAnalysis={handleRequestAnalysis}
            analysisLoadingKey={analysisLoadingKey}
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
