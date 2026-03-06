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
      .then((data) => setHasResume(!!data.uploaded))
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
      <form onSubmit={handleSubmit} className="resume-form">
        <input type="file" accept=".pdf" disabled={uploading} id="resume-file-input" className="resume-file-input" />
        <label htmlFor="resume-file-input" className="resume-file-label">
          Choose PDF
        </label>
        <button type="submit" className="resume-submit-btn" disabled={uploading}>
          {uploading ? 'Uploading…' : 'Upload Resume'}
        </button>
        {hasResume && (
          <button
            type="button"
            className="resume-view-btn"
            onClick={openResumePdf}
            disabled={openingPdf}
          >
            {openingPdf ? 'Opening…' : RESUME_FILENAME}
          </button>
        )}
      </form>
      {message && <p className="resume-msg success">✓ Resume uploaded successfully</p>}
      {error && <p className="resume-msg error">✗ {error}</p>}
    </div>
  )
}
