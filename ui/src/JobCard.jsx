import { useState } from 'react'
import { Button } from 'antd'
import './JobCard.css'

const API = '/api'

function matchLabel(score) {
  if (score == null) return ''
  const n = Number(score)
  if (n >= 70) return 'GOOD MATCH'
  if (n >= 50) return 'MATCH'
  if (n >= 30) return 'LOW MATCH'
  return 'LOW'
}

export function JobCard({ job, isFilteredOut, isAppliedTab, jobKey, onRequestAnalysis, analysisLoading, onMarkApplied, t }) {
  const [markingApplied, setMarkingApplied] = useState(false)
  const score = job.Match_Score != null ? Number(job.Match_Score) : null
  const label = matchLabel(score)
  const isApplied = job.status === 'applied'

  const handleMarkApplied = async () => {
    if (!job.job_id || !onMarkApplied) return
    setMarkingApplied(true)
    try {
      const res = await fetch(`${API}/jobs/${job.job_id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'applied' }),
      })
      if (res.ok) onMarkApplied()
    } finally {
      setMarkingApplied(false)
    }
  }

  return (
    <li className={`job-card ${isFilteredOut ? 'filtered-out' : ''} ${isApplied ? 'job-card-applied' : ''}`}>
      <div className="job-card-main">
        <div className="job-card-left">
          <h3 className="job-title">{job.title || '—'}</h3>
          <p className="job-company">{job.company || '—'}</p>
          <p className="job-meta">
            {[job.location, job.date_posted].filter(Boolean).join(' · ')}
            {job.salary_range && (
              <span className="job-salary"> · {job.salary_range}</span>
            )}
          </p>
          <p className="job-meta">
            {job.site && <span className="job-source-badge">{job.site}</span>}
            {job.is_remote === true || job.is_remote === 'True' ? <span className="job-remote-badge">Remote</span> : null}
            {isApplied && <span className="job-applied-badge">{t.appliedLabel}</span>}
          </p>
          {job['Target Level'] && (
            <p className="job-level">Target: {job['Target Level']}</p>
          )}
          {job.Rejection_Reason && (
            <p className="job-reason">{t.rejectionReason} {job.Rejection_Reason}</p>
          )}
          <div className="job-card-actions">
            {job.job_url && (
              <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="job-link">
                {t.viewJob}
              </a>
            )}
            {job.job_id && onMarkApplied && !isApplied && (
              <Button type="default" size="small" onClick={handleMarkApplied} loading={markingApplied}>
                {t.markApplied}
              </Button>
            )}
            {onRequestAnalysis && jobKey != null && (
              <Button type="primary" size="small" onClick={() => onRequestAnalysis(job, jobKey)} loading={analysisLoading}>
                Analysis
              </Button>
            )}
          </div>
        </div>
        <div className="job-card-score">
          {score != null ? (
            <>
              <div className="score-ring">{score}%</div>
              <span className="score-label">{label}</span>
            </>
          ) : (
            <span className="score-label">—</span>
          )}
        </div>
      </div>
    </li>
  )
}
