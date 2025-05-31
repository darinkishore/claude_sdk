use pyo3::prelude::*;
use pyo3::exceptions::PyException;

// Custom exceptions for Python
pyo3::create_exception!(_core, ClaudeSDKError, PyException);
pyo3::create_exception!(_core, ParseError, ClaudeSDKError);
pyo3::create_exception!(_core, ValidationError, ClaudeSDKError);
pyo3::create_exception!(_core, SessionError, ClaudeSDKError);

pub fn register_exceptions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("ClaudeSDKError", m.py().get_type_bound::<ClaudeSDKError>())?;
    m.add("ParseError", m.py().get_type_bound::<ParseError>())?;
    m.add("ValidationError", m.py().get_type_bound::<ValidationError>())?;
    m.add("SessionError", m.py().get_type_bound::<SessionError>())?;
    Ok(())
}