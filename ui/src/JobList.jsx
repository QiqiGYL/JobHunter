import { JobCard } from './JobCard'

export function JobList({ items, isFilteredOut, isAppliedTab, totalCount, page, totalPages, onPageChange, activeTab, baseIndex = 0, onRequestAnalysis, analysisLoadingKey, onMarkApplied, t }) {
  if (!items?.length && totalCount === 0) {
    return (
      <p className="empty-list">
        {t.emptyListIntro}<code>python hunt.py</code>{t.emptyListOutro}
      </p>
    )
  }
  return (
    <>
      <ul className="job-list">
        {(items || []).map((job, i) => {
          const jobKey = `${activeTab}-${baseIndex + i}`
          return (
            <JobCard
              key={job.job_id || (job.job_url ? `${job.job_url}-${i}` : jobKey)}
              job={job}
              isFilteredOut={isFilteredOut}
              isAppliedTab={isAppliedTab}
              jobKey={jobKey}
              onRequestAnalysis={onRequestAnalysis}
              analysisLoading={analysisLoadingKey === jobKey}
              onMarkApplied={onMarkApplied}
              t={t}
            />
          )
        })}
      </ul>
      {totalPages > 1 && (
        <div className="pagination">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => onPageChange?.(page - 1)}
          >
            {t.prevPage}
          </button>
          <span>Page {page} / {totalPages}</span>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => onPageChange?.(page + 1)}
          >
            {t.nextPage}
          </button>
        </div>
      )}
    </>
  )
}
