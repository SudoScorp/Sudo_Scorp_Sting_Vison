import React, { useState } from 'react'
import PropTypes from 'prop-types'
import axios from 'axios'

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'

const EXTENSION_TO_TYPE = {
  jpg: 'image',
  jpeg: 'image',
  png: 'image',
  gif: 'image',
  bmp: 'image',
  webp: 'image',
  mp4: 'video',
  mov: 'video',
  avi: 'video',
  mkv: 'video',
  webm: 'video',
  wav: 'audio',
  mp3: 'audio',
  m4a: 'audio',
  flac: 'audio',
  ogg: 'audio'
}

const mediaTypeFor = (file) => {
  const ext = file.name.split('.').pop().toLowerCase()
  return EXTENSION_TO_TYPE[ext] || null
}

const buildReportText = (entries) => {
  const lines = [
    'SudoScorpStingVision — Detection Report',
    `Generated: ${new Date().toISOString()}`,
    `Files analyzed: ${entries.length}`,
    ''
  ]

  entries.forEach((entry, index) => {
    const r = entry.results
    const probLines = Object.entries(r.probabilities || {}).map(
      ([cls, prob]) => `    - ${cls}: ${(prob * 100).toFixed(2)}%`
    )
    lines.push('='.repeat(64))
    lines.push(`${index + 1}. ${entry.fileName} (${entry.mediaType})`)
    lines.push(`   Analyzed: ${entry.timestamp}`)
    lines.push(
      `   Verdict: ${r.is_ai_generated ? 'AI-Generated' : 'Likely Real'}`
    )
    lines.push(`   Confidence: ${(r.confidence * 100).toFixed(2)}%`)
    lines.push(`   Predicted class: ${r.predicted_class}`)
    lines.push(`   Source attribution: ${r.source_attribution}`)
    lines.push('   Probabilities:', ...probLines)
    lines.push(
      `   Policy check: ${r.policy_check?.reason} ` +
        `(passed: ${r.policy_check?.policy_passed}, ` +
        `flagged: ${r.policy_check?.flagged_for_review})`
    )
    lines.push(`   Watermark scan checksum: ${r.watermark_scan?.checksum}`)
    lines.push('')
  })

  return lines.join('\n')
}

const Section = ({ title, children }) => {
  return (
    <div style={{ marginTop: '16px' }}>
      <h3 style={{ margin: '0 0 8px' }}>{title}</h3>
      {children}
    </div>
  )
}

Section.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired
}

const App = () => {
  const [file, setFile] = useState(null)
  const [mediaType, setMediaType] = useState(null)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])

  const handleFileChange = (event) => {
    const selected = event.target.files[0]
    setResults(null)
    setError(null)
    setFile(selected || null)
    setMediaType(selected ? mediaTypeFor(selected) : null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!file || !mediaType) return

    setLoading(true)
    setError(null)
    setResults(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/${mediaType}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      )
      setResults(response.data)
      setHistory((prev) => [
        {
          id: `${Date.now()}-${file.name}`,
          fileName: file.name,
          mediaType,
          timestamp: new Date().toISOString(),
          results: response.data
        },
        ...prev
      ])
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(
        detail || 'Error analyzing file. Make sure the backend is running.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadReport = () => {
    const blob = new Blob([buildReportText(history)], {
      type: 'text/plain'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `sudoscorpstingvision-report-${Date.now()}.txt`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div
      style={{
        padding: '20px',
        fontFamily: 'Arial',
        maxWidth: '640px',
        margin: '0 auto'
      }}
    >
      <h1>SudoScorpStingVision</h1>
      <p>
        Upload an image, video, or audio file to check whether it is
        AI-generated.
      </p>

      <form onSubmit={handleSubmit}>
        <input
          type='file'
          onChange={handleFileChange}
          accept='image/*,video/*,audio/*'
        />
        {file && !mediaType && (
          <p style={{ color: '#b00020' }}>
            Unrecognized file type: {file.name}
          </p>
        )}
        {mediaType && (
          <p>
            Detected media type: <strong>{mediaType}</strong>
          </p>
        )}
        <button type='submit' disabled={loading || !file || !mediaType}>
          {loading ? 'Analyzing...' : 'Analyze File'}
        </button>
      </form>

      {error && (
        <div
          style={{
            marginTop: '20px',
            padding: '12px',
            border: '1px solid #b00020',
            color: '#b00020'
          }}
        >
          {error}
        </div>
      )}

      {results && (
        <div
          style={{
            marginTop: '20px',
            padding: '15px',
            border: '1px solid #ccc'
          }}
        >
          <h2 style={{ margin: 0 }}>
            {results.is_ai_generated ? 'AI-Generated' : 'Likely Real'}
          </h2>
          <p>
            <strong>Confidence:</strong> {(results.confidence * 100).toFixed(2)}
            %
          </p>
          <p>
            <strong>Predicted class:</strong> {results.predicted_class}
          </p>
          {results.is_ai_generated && (
            <p>
              <strong>Likely generator:</strong> {results.generator}
            </p>
          )}

          <Section title='Class Probabilities'>
            <ul>
              {Object.entries(results.probabilities || {}).map(
                ([cls, prob]) => (
                  <li key={cls}>
                    {cls}: {(prob * 100).toFixed(2)}%
                  </li>
                )
              )}
            </ul>
          </Section>

          <Section title='Policy Check'>
            <p>{results.policy_check?.reason}</p>
            <p>
              Passed: {String(results.policy_check?.policy_passed)} — Flagged
              for review: {String(results.policy_check?.flagged_for_review)}
            </p>
          </Section>

          <Section title='Watermark / Artifact Scan'>
            <p>Checksum: {results.watermark_scan?.checksum}</p>
            {results.watermark_scan?.watermarks_found?.length > 0 && (
              <ul>
                {results.watermark_scan.watermarks_found.map((w, i) => (
                  <li key={i}>
                    {w.type}: {w.detail} (severity {w.severity})
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title='File Metadata'>
            <pre
              style={{
                background: '#f6f6f6',
                padding: '10px',
                overflowX: 'auto'
              }}
            >
              {JSON.stringify(results.metadata, null, 2)}
            </pre>
          </Section>
        </div>
      )}

      {history.length > 0 && (
        <div style={{ marginTop: '30px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <h2 style={{ margin: 0 }}>Test Results ({history.length})</h2>
            <div>
              <button type='button' onClick={handleDownloadReport}>
                Download Report
              </button>{' '}
              <button type='button' onClick={() => setHistory([])}>
                Clear
              </button>
            </div>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th
                  style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}
                >
                  File
                </th>
                <th
                  style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}
                >
                  Verdict
                </th>
                <th
                  style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}
                >
                  Confidence
                </th>
                <th
                  style={{ textAlign: 'left', borderBottom: '1px solid #ccc' }}
                >
                  Analyzed
                </th>
              </tr>
            </thead>
            <tbody>
              {history.map((entry) => (
                <tr key={entry.id}>
                  <td>
                    {entry.fileName} ({entry.mediaType})
                  </td>
                  <td>
                    {entry.results.is_ai_generated
                      ? 'AI-Generated'
                      : 'Likely Real'}
                  </td>
                  <td>{(entry.results.confidence * 100).toFixed(2)}%</td>
                  <td>{new Date(entry.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default App
