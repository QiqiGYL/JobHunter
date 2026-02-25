import { JobCard } from './JobCard'

export function JobList({ items, isFilteredOut, totalCount, page, totalPages, onPageChange, activeTab, baseIndex = 0, onRequestAnalysis, analysisLoadingKey }) {
  if (!items?.length && totalCount === 0) {
    return <p className="empty-list">暂无数据。请先运行 <code>python hunt.py</code> 生成 job_hunt_results.xlsx。</p>
  }
  return (
    <>
      <ul className="job-list">
        {(items || []).map((job, i) => {
          const jobKey = `${activeTab}-${baseIndex + i}`
          return (
            <JobCard
              key={job.job_url ? `${job.job_url}-${i}` : jobKey}
              job={job}
              isFilteredOut={isFilteredOut}
              jobKey={jobKey}
              onRequestAnalysis={onRequestAnalysis}
              analysisLoading={analysisLoadingKey === jobKey}
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
            上一页
          </button>
          <span>Page {page} / {totalPages}</span>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => onPageChange?.(page + 1)}
          >
            下一页
          </button>
        </div>
      )}
    </>
  )
}
