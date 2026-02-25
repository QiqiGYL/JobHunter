import { useState, useEffect } from 'react'
import { Drawer, Progress, Tag, Table } from 'antd'
import { JobList } from './JobList'
import { ResumeUpload } from './ResumeUpload'
import './App.css'

const API = '/api'

const PAGE_SIZE = 10

export default function App() {
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
      if (!res.ok) {
        setDrawerData({ analysis: null, raw: data.error || res.statusText })
      } else {
        setAnalysisByKey((prev) => ({ ...prev, [jobKey]: { analysis: data.analysis, raw: data.raw } }))
        setDrawerData({ analysis: data.analysis, raw: data.raw })
      }
      setDrawerJob(job)
      setDrawerOpen(true)
    } catch (e) {
      setDrawerData({ analysis: null, raw: e.message || '请求失败' })
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
      <header className="header">
        <h1>JobHunter</h1>
        <p className="subtitle">职位列表按 Match Score 排序 · 数据来自 job_hunt_results.xlsx</p>
        <ResumeUpload onUploaded={handleResumeUploaded} />
      </header>

      {loading && <div className="loading">加载中…</div>}
      {error && (
        <div className="error">
          {error}
          <button type="button" onClick={fetchJobs}>重试</button>
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
              保留的职位 (Jobs)
            </button>
            <button
              type="button"
              className={activeTab === 'filteredOut' ? 'active' : ''}
              onClick={() => handleTabChange('filteredOut')}
            >
              已筛除 (Filtered Out)
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
          />
        </section>
      )}

      <Drawer
        title={drawerJob ? `${drawerJob.title} @ ${drawerJob.company}` : 'ATS 分析'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={560}
        destroyOnClose={false}
      >
        {drawerData && (
          <AnalysisDrawerContent data={drawerData} />
        )}
      </Drawer>
    </div>
  )
}

function AnalysisDrawerContent({ data }) {
  const { analysis, raw } = data
  if (analysis) {
    const score = analysis.ats_match_score != null ? Number(analysis.ats_match_score) : null
    const keywords = analysis.missing_keywords || []
    const edits = analysis.resume_edits || []
    const editColumns = [
      { title: '原描述', dataIndex: 'original', key: 'original', width: '45%' },
      { title: '优化后', dataIndex: 'optimized', key: 'optimized', width: '55%', render: (t) => <span className="resume-edit-optimized">{t}</span> },
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
            <h4>缺失关键词 (Gap Analysis)</h4>
            <div className="analysis-tags">
              {keywords.map((k, i) => (
                <Tag key={i} color="red">{k}</Tag>
              ))}
            </div>
          </div>
        )}
        {edits.length > 0 && (
          <div className="analysis-section">
            <h4>简历手术 (Resume Surgery)</h4>
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
      <p className="analysis-raw">无结构化结果，原始回复：</p>
      <pre className="analysis-raw-pre">{raw || '—'}</pre>
    </div>
  )
}
