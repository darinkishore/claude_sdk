use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::path::PathBuf;
use std::sync::Arc;

use crate::execution::{
    ClaudeExecution as RustClaudeExecution, ClaudePrompt as RustClaudePrompt,
    Conversation as RustConversation, EnvironmentSnapshot as RustEnvironmentSnapshot,
    Transition as RustTransition, Workspace as RustWorkspace,
};

/// Python wrapper for Workspace
#[pyclass(name = "Workspace")]
pub struct PyWorkspace {
    inner: Arc<RustWorkspace>,
}

#[pymethods]
impl PyWorkspace {
    #[new]
    fn new(path: String) -> PyResult<Self> {
        let workspace = RustWorkspace::new(PathBuf::from(path))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(Self {
            inner: Arc::new(workspace),
        })
    }

    #[getter]
    fn path(&self) -> String {
        self.inner.path().display().to_string()
    }

    fn snapshot(&self) -> PyResult<PyEnvironmentSnapshot> {
        let snapshot = self
            .inner
            .snapshot()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(PyEnvironmentSnapshot { inner: snapshot })
    }

    fn snapshot_with_session(&self, session_id: &str) -> PyResult<PyEnvironmentSnapshot> {
        let snapshot = self
            .inner
            .snapshot_with_session(session_id)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(PyEnvironmentSnapshot { inner: snapshot })
    }

    fn set_skip_permissions(&self, skip: bool) -> PyResult<()> {
        // We need mutable access to workspace, but PyWorkspace holds Arc<RustWorkspace>
        // This is a limitation of the current design - we'd need Arc<Mutex<RustWorkspace>>
        // For now, let's document this limitation
        Err(PyErr::new::<pyo3::exceptions::PyNotImplementedError, _>(
            "set_skip_permissions not yet implemented due to Arc wrapper",
        ))
    }
}

/// Python wrapper for Conversation
#[pyclass(name = "Conversation")]
pub struct PyConversation {
    inner: RustConversation,
}

#[pymethods]
impl PyConversation {
    #[new]
    #[pyo3(signature = (workspace, record=true))]
    fn new(workspace: &PyWorkspace, record: bool) -> PyResult<Self> {
        let conversation = if record {
            RustConversation::new_with_options(workspace.inner.clone(), true)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?
        } else {
            RustConversation::new(workspace.inner.clone())
        };
        Ok(Self {
            inner: conversation,
        })
    }

    fn send(&mut self, message: &str) -> PyResult<PyTransition> {
        let transition = self
            .inner
            .send(message)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(PyTransition { inner: transition })
    }

    fn history(&self) -> Vec<PyTransition> {
        self.inner
            .history()
            .iter()
            .map(|t| PyTransition { inner: t.clone() })
            .collect()
    }

    #[getter]
    fn id(&self) -> String {
        self.inner.id().to_string()
    }

    #[getter]
    fn session_ids(&self) -> Vec<String> {
        self.inner.session_ids().to_vec()
    }

    #[getter]
    fn total_cost(&self) -> f64 {
        self.inner.total_cost()
    }

    fn last_transition(&self) -> Option<PyTransition> {
        self.inner
            .last_transition()
            .map(|t| PyTransition { inner: t.clone() })
    }

    fn tools_used(&self) -> Vec<String> {
        self.inner.tools_used()
    }

    fn save(&self, path: &str) -> PyResult<()> {
        self.inner
            .save(&PathBuf::from(path))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    #[staticmethod]
    #[pyo3(signature = (path, workspace, record=true))]
    fn load(path: &str, workspace: &PyWorkspace, record: bool) -> PyResult<Self> {
        let conversation =
            RustConversation::load(&PathBuf::from(path), workspace.inner.clone(), record)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(Self {
            inner: conversation,
        })
    }
}

/// Python wrapper for Transition
#[pyclass(name = "Transition")]
#[derive(Clone)]
pub struct PyTransition {
    inner: RustTransition,
}

#[pymethods]
impl PyTransition {
    #[getter]
    fn id(&self) -> String {
        self.inner.id.to_string()
    }

    #[getter]
    fn before(&self) -> PyEnvironmentSnapshot {
        PyEnvironmentSnapshot {
            inner: self.inner.before.clone(),
        }
    }

    #[getter]
    fn after(&self) -> PyEnvironmentSnapshot {
        PyEnvironmentSnapshot {
            inner: self.inner.after.clone(),
        }
    }

    #[getter]
    fn prompt(&self) -> PyClaudePrompt {
        PyClaudePrompt {
            inner: self.inner.prompt.clone(),
        }
    }

    #[getter]
    fn execution(&self) -> PyClaudeExecution {
        PyClaudeExecution {
            inner: self.inner.execution.clone(),
        }
    }

    #[getter]
    fn recorded_at(&self) -> String {
        self.inner.recorded_at.to_rfc3339()
    }

    fn new_messages(&self) -> PyResult<Py<PyAny>> {
        Python::with_gil(|py| {
            let messages = self.inner.new_messages();
            // Convert to Python list of message dicts
            let py_list = pyo3::types::PyList::empty(py);
            for msg in messages {
                // Convert MessageRecord to dict
                let dict = PyDict::new(py);
                dict.set_item("role", msg.message.role.to_string())?;
                dict.set_item("timestamp", msg.timestamp.to_rfc3339())?;
                // Add more fields as needed
                py_list.append(dict)?;
            }
            Ok(py_list.into())
        })
    }

    fn tools_used(&self) -> Vec<String> {
        self.inner.tools_used()
    }

    fn has_tool_errors(&self) -> bool {
        self.inner.has_tool_errors()
    }
}

/// Python wrapper for ClaudePrompt
#[pyclass(name = "ClaudePrompt")]
#[derive(Clone)]
pub struct PyClaudePrompt {
    inner: RustClaudePrompt,
}

#[pymethods]
impl PyClaudePrompt {
    #[new]
    #[pyo3(signature = (text, resume_session_id=None))]
    fn new(text: String, resume_session_id: Option<String>) -> Self {
        let prompt = RustClaudePrompt {
            text,
            continue_session: false,
            resume_session_id,
        };
        Self { inner: prompt }
    }

    #[getter]
    fn text(&self) -> &str {
        &self.inner.text
    }

    #[getter]
    fn resume_session_id(&self) -> Option<String> {
        self.inner.resume_session_id.clone()
    }
}

/// Python wrapper for ClaudeExecution
#[pyclass(name = "ClaudeExecution")]
#[derive(Clone)]
pub struct PyClaudeExecution {
    inner: RustClaudeExecution,
}

#[pymethods]
impl PyClaudeExecution {
    #[getter]
    fn session_id(&self) -> &str {
        &self.inner.session_id
    }

    #[getter]
    fn response(&self) -> &str {
        &self.inner.response
    }

    #[getter]
    fn cost(&self) -> f64 {
        self.inner.cost
    }

    #[getter]
    fn duration_ms(&self) -> u64 {
        self.inner.duration_ms
    }
}

/// Python wrapper for EnvironmentSnapshot
#[pyclass(name = "EnvironmentSnapshot")]
#[derive(Clone)]
pub struct PyEnvironmentSnapshot {
    inner: RustEnvironmentSnapshot,
}

#[pymethods]
impl PyEnvironmentSnapshot {
    #[getter]
    fn files(&self) -> PyResult<Py<PyDict>> {
        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            for (path, content) in &self.inner.files {
                dict.set_item(path.display().to_string(), content)?;
            }
            Ok(dict.into())
        })
    }

    #[getter]
    fn session_file(&self) -> String {
        self.inner.session_file.display().to_string()
    }

    #[getter]
    fn session_id(&self) -> Option<String> {
        self.inner.session_id.clone()
    }

    #[getter]
    fn timestamp(&self) -> String {
        self.inner.timestamp.to_rfc3339()
    }
}

/// Register execution module types
pub fn register_execution_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyWorkspace>()?;
    m.add_class::<PyConversation>()?;
    m.add_class::<PyTransition>()?;
    m.add_class::<PyClaudePrompt>()?;
    m.add_class::<PyClaudeExecution>()?;
    m.add_class::<PyEnvironmentSnapshot>()?;
    Ok(())
}
