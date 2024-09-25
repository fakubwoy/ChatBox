import React, { useState, useEffect } from 'react';

export function FileUpload({ apiUrl }) {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const uploadFile = async () => {
    if (!file) {
      alert('Please select a file.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${apiUrl}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        alert(result.message);
        setFile(null);
      } else {
        alert('File upload failed');
      }
    } catch (error) {
      alert(`An error occurred: ${error.message}`);
    }
  };

  return (
    <div className="section file-section">
      <h2>File Upload</h2>
      <label htmlFor="fileInput" className="custom-file-upload">
        {file ? file.name : 'Choose File'}
      </label>
      <input type="file" id="fileInput" onChange={handleFileChange} />
      <button className="action-button" onClick={uploadFile}>Upload</button>
    </div>
  );
}

export function FileDownload({ apiUrl }) {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');

  useEffect(() => {
    updateFileList();
  }, []); 

  const updateFileList = async () => {
    try {
      const response = await fetch(`${apiUrl}/list-files`);
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files);
      } else {
        alert('Failed to retrieve file list');
      }
    } catch (error) {
      alert(`An error occurred: ${error.message}`);
    }
  };

  const downloadFile = async () => {
    if (!selectedFile) {
      alert('Please select a file.');
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/download/${encodeURIComponent(selectedFile)}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = selectedFile;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        alert('Failed to download file');
      }
    } catch (error) {
      alert(`An error occurred: ${error.message}`);
    }
  };

  return (
    <div className="section file-section">
      <h2>File Download</h2>
      <select
        value={selectedFile}
        onChange={(e) => setSelectedFile(e.target.value)}
      >
        <option value="">Select a file</option>
        {files.map((file, index) => (
          <option key={index} value={file}>{file}</option>
        ))}
      </select>
      <button className="action-button" onClick={downloadFile}>Download</button>
    </div>
  );
}