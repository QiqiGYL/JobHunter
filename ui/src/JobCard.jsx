import { Button } from 'antd'
import './JobCard.css'

function matchLabel(score) {
  if (score == null) return ''
  const n = Number(score)
  if (n >= 70) return 'GOOD MATCH'
  if (n >= 50) return 'MATCH'
  if (n >= 30) return 'LOW MATCH'
  return 'LOW'
}

export function JobCard({ job, isFilteredOut, jobKey, onRequestAnalysis, analysisLoading }) {
  const score = job.Match_Score != null ? Number(job.Match_Score) : null
  const label = matchLabel(score)

  return (
    <li className={`job-card ${isFilteredOut ? 'filtered-out' : ''}`}>
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
          {job['Target Level'] && (
            <p className="job-level">Target: {job['Target Level']}</p>
          )}
          {job.Rejection_Reason && (
            <p className="job-reason">筛除原因: {job.Rejection_Reason}</p>
          )}
          <div className="job-card-actions">
            {job.job_url && (
              <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="job-link">
                查看职位
              </a>
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
