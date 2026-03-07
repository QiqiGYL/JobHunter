import { useState, useEffect } from 'react'

const API = '/api'
const RESUME_FILENAME = 'current_resume.pdf'

const UPLOAD_STRINGS = {
  en: {
    choosePdf: 'Choose PDF',
    upload: 'Upload Resume',
    uploading: 'Uploading…',
    opening: 'Opening…',
    noFile: 'Please select a PDF file first',
    pdfOnly: 'Only PDF files are supported',
    uploadOk: 'Resume uploaded successfully. It will be used on the next run of hunt.py.',
    uploadFail: 'Upload failed',
    openFail: 'Failed to open resume',
    notFound: 'Resume file not found',
  },
  zh: {
    choosePdf: 'Choose PDF',
    upload: 'Upload Resume',
    uploading: 'Uploading…',
    opening: 'Opening…',
    noFile: '请选择 PDF 文件',
    pdfOnly: '仅支持 PDF',
    uploadOk: '简历上传成功，已保存为 data/uploads/current_resume.pdf。下次运行 hunt.py 可使用该简历。',
    uploadFail: '上传失败',
    openFail: '打开简历失败',
    notFound: '未找到简历文件',
  },
}

export function ResumeUpload({ onUploaded, lang = 'en' }) {
  const s = UPLOAD_STRINGS[lang] || UPLOAD_STRINGS.en
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)
  const [hasResume, setHasResume] = useState(false)
  const [openingPdf, setOpeningPdf] = useState(false)
  const [selectedFileName, setSelectedFileName] = useState(null)

  const openResumePdf = async () => {
    setError(null)
    setOpeningPdf(true)
    try {
      const res = await fetch(`${API}/resume/file`)
      if (!res.ok) {
        setError(s.notFound)
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank', 'noopener,noreferrer')
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (e) {
      setError(e.message || s.openFail)
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

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    setSelectedFileName(file ? file.name : null)
    setError(null)
    setMessage(null)
  }

  const handleClearFile = () => {
    setSelectedFileName(null)
    setError(null)
    const input = document.getElementById('resume-file-input')
    if (input) input.value = ''
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const input = e.target.querySelector('input[type="file"]')
    const file = input?.files?.[0]
    if (!file) {
      setError(s.noFile)
      return
    }
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError(s.pdfOnly)
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
      setMessage(s.uploadOk)
      setHasResume(true)
      setSelectedFileName(null)
      onUploaded?.()
    } catch (e) {
      setError(e.message || s.uploadFail)
    } finally {
      setUploading(false)
      input.value = ''
    }
  }

  return (
    <div className="resume-upload">
      <form onSubmit={handleSubmit} className="resume-form">
        <input
          type="file"
          accept=".pdf"
          disabled={uploading}
          id="resume-file-input"
          className="resume-file-input"
          onChange={handleFileChange}
        />
        <label htmlFor="resume-file-input" className="resume-file-label">
          {s.choosePdf}
        </label>
        {selectedFileName && (
          <span className="resume-selected-file">
            📄 {selectedFileName}
            <button type="button" className="resume-clear-btn" onClick={handleClearFile} title="Remove">×</button>
          </span>
        )}
        <button type="submit" className="resume-submit-btn" disabled={uploading}>
          {uploading ? s.uploading : s.upload}
        </button>
        {hasResume && (
          <button
            type="button"
            className="resume-view-btn"
            onClick={openResumePdf}
            disabled={openingPdf}
          >
            {openingPdf ? s.opening : RESUME_FILENAME}
          </button>
        )}
      </form>
      {message && <p className="resume-msg success">✓ {message}</p>}
      {error && <p className="resume-msg error">✗ {error}</p>}
    </div>
  )
}
