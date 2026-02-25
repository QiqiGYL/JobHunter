import { useState, useEffect } from 'react'

const API = '/api'
const RESUME_FILENAME = 'current_resume.pdf'

export function ResumeUpload({ onUploaded }) {
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)
  const [hasResume, setHasResume] = useState(false)
  const [openingPdf, setOpeningPdf] = useState(false)

  const openResumePdf = async () => {
    setError(null)
    setOpeningPdf(true)
    try {
      const res = await fetch(`${API}/resume/file`)
      if (!res.ok) {
        // #region agent log
        fetch('http://127.0.0.1:7570/ingest/9d152392-e621-4d1c-85bb-5369d73773fd', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': '04911f' }, body: JSON.stringify({ sessionId: '04911f', location: 'ResumeUpload.jsx:openResumePdf 404', message: 'resume/file not ok', data: { status: res.status, ok: res.ok, url: res.url }, timestamp: Date.now(), hypothesisId: 'B' }) }).catch(() => { });
        // #endregion
        setError('未找到简历文件')
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank', 'noopener,noreferrer')
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (e) {
      setError(e.message || '打开简历失败')
    } finally {
      setOpeningPdf(false)
    }
  }

  useEffect(() => {
    fetch(`${API}/resume/status`, { cache: 'no-store' })
      .then((res) => res.json().catch(() => ({})))
      .then((data) => {
        // #region agent log
        fetch('http://127.0.0.1:7570/ingest/9d152392-e621-4d1c-85bb-5369d73773fd', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': '04911f' }, body: JSON.stringify({ sessionId: '04911f', location: 'ResumeUpload.jsx:useEffect status', message: 'status response', data: { uploaded: !!data.uploaded }, timestamp: Date.now(), hypothesisId: 'D' }) }).catch(() => { });
        // #endregion
        setHasResume(!!data.uploaded)
      })
      .catch(() => setHasResume(false))
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const input = e.target.querySelector('input[type="file"]')
    const file = input?.files?.[0]
    if (!file) {
      setError('请选择 PDF 文件')
      return
    }
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('仅支持 PDF')
      return
    }
    setError(null)
    setMessage(null)
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch(`${API}/resume`, { method: 'POST', body: form })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setError(data.error || res.statusText)
        return
      }
      setMessage('简历上传成功，已保存为 data/uploads/current_resume.pdf。下次运行 hunt.py 可使用该简历。')
      setHasResume(true)
      onUploaded?.()
    } catch (e) {
      setError(e.message || '上传失败')
    } finally {
      setUploading(false)
      input.value = ''
    }
  }

  return (
    <div className="resume-upload">
      {hasResume && (
        <p className="resume-current">
          当前简历:{' '}
          <button
            type="button"
            className="resume-current-link"
            onClick={openResumePdf}
            disabled={openingPdf}
          >
            {openingPdf ? '打开中…' : RESUME_FILENAME}
          </button>
        </p>
      )}
      <form onSubmit={handleSubmit}>
        <label className="resume-label">
          <span>上传简历 (PDF)</span>
          <input type="file" accept=".pdf" disabled={uploading} />
        </label>
        <button type="submit" disabled={uploading}>
          {uploading ? '上传中…' : 'Upload resume'}
        </button>
      </form>
      {message && <p className="resume-msg success">{message}</p>}
      {error && <p className="resume-msg error">{error}</p>}
    </div>
  )
}
