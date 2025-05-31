use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use serde_json::Value;
use chrono::{DateTime, Utc};

/// Convert a serde_json::Value to a Python object
pub fn json_to_py(py: Python<'_>, value: &Value) -> PyResult<PyObject> {
    match value {
        Value::Null => Ok(py.None()),
        Value::Bool(b) => Ok(b.to_object(py)),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.to_object(py))
            } else if let Some(u) = n.as_u64() {
                Ok(u.to_object(py))
            } else if let Some(f) = n.as_f64() {
                Ok(f.to_object(py))
            } else {
                Ok(py.None())
            }
        }
        Value::String(s) => Ok(s.to_object(py)),
        Value::Array(arr) => {
            let list = PyList::empty_bound(py);
            for item in arr {
                list.append(json_to_py(py, item)?)?;
            }
            Ok(list.into())
        }
        Value::Object(map) => {
            let dict = PyDict::new_bound(py);
            for (key, val) in map {
                dict.set_item(key, json_to_py(py, val)?)?;
            }
            Ok(dict.into())
        }
    }
}

/// Convert a chrono DateTime to a Python datetime object
pub fn datetime_to_py(py: Python<'_>, dt: DateTime<Utc>) -> PyResult<PyObject> {
    // PyO3 datetime support requires chrono-tz feature or manual conversion
    // For now, return the ISO string representation
    Ok(dt.to_rfc3339().to_object(py))
}