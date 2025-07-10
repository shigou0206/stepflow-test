/// 解析 OpenAPI 内容（调试版）
pub fn parse_openapi_content_debug(&self, content: &str) -> Result<OpenApi30Spec, ServiceError> {
    // 打印内容前100个字符，帮助调试
    println!("Content preview: {}", &content[..content.len().min(100)]);
    println!("Content length: {}", content.len());
    
    // 检测内容类型
    let trimmed = content.trim();
    let is_likely_json = trimmed.starts_with('{') || trimmed.starts_with('[');
    let is_likely_yaml = !is_likely_json && (trimmed.contains(':') || trimmed.contains('-'));
    
    println!("Content type detection: JSON={}, YAML={}", is_likely_json, is_likely_yaml);
    
    // 根据内容类型优先选择解析器
    if is_likely_json {
        println!("Attempting JSON parse first...");
        match serde_json::from_str::<OpenApi30Spec>(content) {
            Ok(spec) => {
                println!("JSON parse successful!");
                return Ok(spec);
            }
            Err(json_err) => {
                println!("JSON parse failed: {:?}", json_err);
                
                // 尝试 YAML 作为备选
                println!("Attempting YAML parse as fallback...");
                match serde_yaml::from_str::<OpenApi30Spec>(content) {
                    Ok(spec) => {
                        println!("YAML parse successful!");
                        return Ok(spec);
                    }
                    Err(yaml_err) => {
                        println!("YAML parse also failed: {:?}", yaml_err);
                        return Err(ServiceError::ParseError(format!(
                            "JSON parse failed: {:?}, YAML parse failed: {:?}",
                            json_err, yaml_err
                        )));
                    }
                }
            }
        }
    } else {
        // 优先尝试 YAML
        println!("Attempting YAML parse first...");
        match serde_yaml::from_str::<OpenApi30Spec>(content) {
            Ok(spec) => {
                println!("YAML parse successful!");
                return Ok(spec);
            }
            Err(yaml_err) => {
                println!("YAML parse failed: {:?}", yaml_err);
                
                // 尝试 JSON 作为备选
                println!("Attempting JSON parse as fallback...");
                match serde_json::from_str::<OpenApi30Spec>(content) {
                    Ok(spec) => {
                        println!("JSON parse successful!");
                        return Ok(spec);
                    }
                    Err(json_err) => {
                        println!("JSON parse also failed: {:?}", json_err);
                        return Err(ServiceError::ParseError(format!(
                            "YAML parse failed: {:?}, JSON parse failed: {:?}",
                            yaml_err, json_err
                        )));
                    }
                }
            }
        }
    }
} 