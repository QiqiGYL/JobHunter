import { useState, useEffect } from 'react'
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
          />
        </section>
      )}
    </div>
  )
}
