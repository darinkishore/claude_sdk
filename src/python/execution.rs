use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use crate::execution::{
    ClaudeExecution as RustClaudeExecution, ClaudePrompt as RustClaudePrompt,
    Conversation as RustConversation, EnvironmentSnapshot as RustEnvironmentSnapshot,
    Transition as RustTransition, Workspace as RustWorkspace,
};

/// Python wrapper for Workspace
#[pyclass(name = "Workspace")]
pub struct PyWorkspace {
    inner: Arc<Mutex<RustWorkspace>>,
}

#[pymethods]
impl PyWorkspace {
    #[new]
    fn new(path: String) -> PyResult<Self> {
        let workspace = RustWorkspace::new(PathBuf::from(path))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(Self {
            inner: Arc::new(Mutex::new(workspace)),
        })
    }

    #[getter]
    fn path(&self) -> PyResult<String> {
        let workspace = self.inner.lock()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock error: {}", e)))?;
        Ok(workspace.path().display().to_string())
    }

    fn snapshot(&self) -> PyResult<PyEnvironmentSnapshot> {
        let workspace = self.inner.lock()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock error: {}", e)))?;
        let snapshot = workspace
            .snapshot()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(PyEnvironmentSnapshot { inner: snapshot })
    }

    fn snapshot_with_session(&self, session_id: &str) -> PyResult<PyEnvironmentSnapshot> {
        let workspace = self.inner.lock()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock error: {}", e)))?;
        let snapshot = workspace
            .snapshot_with_session(session_id)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(PyEnvironmentSnapshot { inner: snapshot })
    }

    fn set_skip_permissions(&self, skip: bool) -> PyResult<()> {
        let mut workspace = self.inner.lock()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock error: {}", e)))?;
        workspace.set_skip_permissions(skip);
        Ok(())
    }

    fn set_model(&self, model: Option<String>) -> PyResult<()> {
        let mut workspace = self.inner.lock()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock error: {}", e)))?;
        workspace.set_model(model);
        Ok(())
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
        // Need to clone the Arc<Mutex<>> for conversation, but conversation expects Arc<Workspace>
        // We'll need to restructure this, but for now let's create a new pattern
        let workspace_path = {
            let ws = workspace.inner.lock()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock error: {}", e)))?;
            ws.path().clone()
        };
        
        // Create a new workspace for the conversation - this is a limitation we can improve later
        let rust_workspace = RustWorkspace::new(workspace_path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let workspace_arc = Arc::new(rust_workspace);
        
        let conversation = if record {
            RustConversation::new_with_options(workspace_arc, true)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?
        } else {
            RustConversation::new(workspace_arc)
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
        // Get workspace path for creating new workspace instance
        let workspace_path = {
            let ws = workspace.inner.lock()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Lock error: {}", e)))?;
            ws.path().clone()
        };
        
        // Create a new workspace for the conversation
        let rust_workspace = RustWorkspace::new(workspace_path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let workspace_arc = Arc::new(rust_workspace);
        
        let conversation = RustConversation::load(&PathBuf::from(path), workspace_arc, record)
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
    fn session_after(&self) -> Option<crate::python::classes::Session> {
        self
            .inner
            .after
            .session
            .as_ref()
            .map(|s| crate::python::classes::Session::from_rust_session((**s).clone()))
    }

    #[getter]
    fn recorded_at(&self) -> String {
        self.inner.recorded_at.to_rfc3339()
    }

    fn new_messages(&self) -> Vec<crate::python::classes::Message> {
        // Each MessageRecord -> fully-typed Message
        self.inner
            .new_messages()
            .into_iter()
            .map(crate::python::classes::Message::from_rust_message)
            .collect()
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
