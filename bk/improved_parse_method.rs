/// 解析 OpenAPI 内容（改进版）
pub fn parse_openapi_content(&self, content: &str) -> Result<OpenApi30Spec, ServiceError> {
    // 首先尝试 JSON 解析
    match serde_json::from_str::<OpenApi30Spec>(content) {
        Ok(spec) => return Ok(spec),
        Err(json_err) => {
            // 记录 JSON 解析错误
            eprintln!("JSON parse error: {:?}", json_err);
            
            // 尝试 YAML 解析
            match serde_yaml::from_str::<OpenApi30Spec>(content) {
                Ok(spec) => return Ok(spec),
                Err(yaml_err) => {
                    // 记录 YAML 解析错误
                    eprintln!("YAML parse error: {:?}", yaml_err);
                    
                    // 返回详细的错误信息
                    Err(ServiceError::ParseError(format!(
                        "Failed to parse content as JSON or YAML. JSON error: {:?}, YAML error: {:?}",
                        json_err, yaml_err
                    )))
                }
            }
        }
    }
} 