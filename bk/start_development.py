#!/usr/bin/env python3
"""
StepFlow Gateway 开发启动工具
帮助快速开始第一阶段的开发工作
"""

import os
import sys
import json
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DevelopmentTask:
    """开发任务"""
    id: str
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    status: str  # "todo", "in_progress", "done"
    estimated_hours: int
    dependencies: List[str]
    notes: str = ""

class DevelopmentPlanner:
    """开发计划器"""
    
    def __init__(self):
        self.tasks = self._initialize_tasks()
        self.current_phase = "phase1"
        
    def _initialize_tasks(self) -> Dict[str, DevelopmentTask]:
        """初始化开发任务"""
        return {
            # 第一阶段：核心功能
            "api_registry_struct": DevelopmentTask(
                id="api_registry_struct",
                title="设计 API 注册数据结构",
                description="定义 ApiRegistry 和 RegisteredApi 结构体，实现内存存储",
                priority="high",
                status="todo",
                estimated_hours=2,
                dependencies=[],
                notes="这是整个系统的基础，需要仔细设计"
            ),
            "api_register_endpoint": DevelopmentTask(
                id="api_register_endpoint",
                title="实现 API 注册端点",
                description="POST /v1/apis/register - 注册新的 OpenAPI 文档",
                priority="high",
                status="todo",
                estimated_hours=4,
                dependencies=["api_registry_struct"],
                notes="需要处理 OpenAPI 解析和验证"
            ),
            "api_list_endpoint": DevelopmentTask(
                id="api_list_endpoint",
                title="实现 API 列表端点",
                description="GET /v1/apis - 列出所有注册的 API",
                priority="high",
                status="todo",
                estimated_hours=2,
                dependencies=["api_registry_struct"],
                notes="支持分页和过滤"
            ),
            "api_detail_endpoint": DevelopmentTask(
                id="api_detail_endpoint",
                title="实现 API 详情端点",
                description="GET /v1/apis/{api_id} - 获取特定 API 详情",
                priority="high",
                status="todo",
                estimated_hours=2,
                dependencies=["api_registry_struct"],
                notes="包含端点统计信息"
            ),
            "api_delete_endpoint": DevelopmentTask(
                id="api_delete_endpoint",
                title="实现 API 删除端点",
                description="DELETE /v1/apis/{api_id} - 删除注册的 API",
                priority="high",
                status="todo",
                estimated_hours=2,
                dependencies=["api_registry_struct"],
                notes="需要清理相关资源"
            ),
            "path_matching": DevelopmentTask(
                id="path_matching",
                title="实现路径匹配系统",
                description="解析 OpenAPI 路径模板，支持参数提取",
                priority="high",
                status="todo",
                estimated_hours=6,
                dependencies=["api_register_endpoint"],
                notes="这是代理功能的核心"
            ),
            "basic_proxy": DevelopmentTask(
                id="basic_proxy",
                title="实现基础代理功能",
                description="/{api_id}/{path:.*} - 动态代理端点",
                priority="high",
                status="todo",
                estimated_hours=8,
                dependencies=["path_matching"],
                notes="支持所有 HTTP 方法，转发请求和响应"
            ),
            "error_handling": DevelopmentTask(
                id="error_handling",
                title="实现统一错误处理",
                description="定义错误类型，统一错误响应格式",
                priority="medium",
                status="todo",
                estimated_hours=4,
                dependencies=["basic_proxy"],
                notes="提高系统的健壮性"
            ),
            
            # 第二阶段：验证和优化
            "parameter_validation": DevelopmentTask(
                id="parameter_validation",
                title="实现参数验证系统",
                description="验证路径参数、查询参数、请求体",
                priority="medium",
                status="todo",
                estimated_hours=8,
                dependencies=["basic_proxy"],
                notes="确保 API 调用的安全性"
            ),
            "logging_system": DevelopmentTask(
                id="logging_system",
                title="实现日志系统",
                description="请求日志、错误日志、性能指标",
                priority="medium",
                status="todo",
                estimated_hours=4,
                dependencies=["basic_proxy"],
                notes="便于调试和监控"
            ),
            
            # 第三阶段：前端集成
            "form_generation": DevelopmentTask(
                id="form_generation",
                title="实现动态表单生成",
                description="根据 OpenAPI 操作生成表单模式",
                priority="low",
                status="todo",
                estimated_hours=6,
                dependencies=["parameter_validation"],
                notes="支持前端动态界面"
            ),
            "swagger_integration": DevelopmentTask(
                id="swagger_integration",
                title="集成 Swagger UI",
                description="动态 API 文档界面",
                priority="low",
                status="todo",
                estimated_hours=4,
                dependencies=["form_generation"],
                notes="提供交互式 API 测试"
            )
        }
    
    def show_current_phase(self):
        """显示当前阶段的任务"""
        print(f"\n🎯 当前阶段：{self.current_phase.upper()}")
        print("=" * 50)
        
        phase_tasks = {
            "phase1": ["api_registry_struct", "api_register_endpoint", "api_list_endpoint", 
                      "api_detail_endpoint", "api_delete_endpoint", "path_matching", 
                      "basic_proxy", "error_handling"],
            "phase2": ["parameter_validation", "logging_system"],
            "phase3": ["form_generation", "swagger_integration"]
        }
        
        current_tasks = phase_tasks.get(self.current_phase, [])
        
        for task_id in current_tasks:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                status_icon = {
                    "todo": "⏳",
                    "in_progress": "🔄",
                    "done": "✅"
                }.get(task.status, "❓")
                
                priority_icon = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(task.priority, "⚪")
                
                print(f"{status_icon} {priority_icon} {task.title}")
                print(f"   描述: {task.description}")
                print(f"   状态: {task.status}")
                print(f"   预估时间: {task.estimated_hours} 小时")
                if task.dependencies:
                    print(f"   依赖: {', '.join(task.dependencies)}")
                if task.notes:
                    print(f"   备注: {task.notes}")
                print()
    
    def show_next_task(self):
        """显示下一个推荐任务"""
        print("\n📋 推荐的下一个任务：")
        print("=" * 30)
        
        # 找到可以开始的任务（依赖已完成）
        available_tasks = []
        for task_id, task in self.tasks.items():
            if task.status == "todo":
                # 检查依赖是否都已完成
                dependencies_met = True
                for dep_id in task.dependencies:
                    if dep_id not in self.tasks or self.tasks[dep_id].status != "done":
                        dependencies_met = False
                        break
                
                if dependencies_met:
                    available_tasks.append(task)
        
        if not available_tasks:
            print("🎉 所有任务都已完成！")
            return
        
        # 按优先级排序
        priority_order = {"high": 1, "medium": 2, "low": 3}
        available_tasks.sort(key=lambda t: priority_order.get(t.priority, 4))
        
        next_task = available_tasks[0]
        print(f"🔴 {next_task.title}")
        print(f"   描述: {next_task.description}")
        print(f"   预估时间: {next_task.estimated_hours} 小时")
        print(f"   优先级: {next_task.priority}")
        if next_task.notes:
            print(f"   备注: {next_task.notes}")
    
    def update_task_status(self, task_id: str, status: str):
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            print(f"✅ 任务 '{self.tasks[task_id].title}' 状态已更新为: {status}")
        else:
            print(f"❌ 任务 '{task_id}' 不存在")
    
    def show_progress(self):
        """显示整体进度"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for task in self.tasks.values() if task.status == "done")
        in_progress_tasks = sum(1 for task in self.tasks.values() if task.status == "in_progress")
        
        progress_percentage = (completed_tasks / total_tasks) * 100
        
        print(f"\n📊 项目进度")
        print("=" * 20)
        print(f"总任务数: {total_tasks}")
        print(f"已完成: {completed_tasks} ✅")
        print(f"进行中: {in_progress_tasks} 🔄")
        print(f"待开始: {total_tasks - completed_tasks - in_progress_tasks} ⏳")
        print(f"完成度: {progress_percentage:.1f}%")
        
        # 显示进度条
        bar_length = 20
        filled_length = int(bar_length * progress_percentage / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"进度条: [{bar}] {progress_percentage:.1f}%")
    
    def generate_rust_template(self, task_id: str):
        """生成 Rust 代码模板"""
        templates = {
            "api_registry_struct": """
// src/models/api_registry.rs
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use crate::openapi::OpenApi30Spec;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiRegistry {
    pub apis: HashMap<String, RegisteredApi>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegisteredApi {
    pub id: String,
    pub name: String,
    pub version: String,
    pub spec: OpenApi30Spec,
    pub base_url: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl ApiRegistry {
    pub fn new() -> Self {
        Self {
            apis: HashMap::new(),
        }
    }
    
    pub fn register_api(&mut self, name: String, version: String, spec: OpenApi30Spec, base_url: String) -> String {
        let id = uuid::Uuid::new_v4().to_string();
        let now = Utc::now();
        
        let api = RegisteredApi {
            id: id.clone(),
            name,
            version,
            spec,
            base_url,
            created_at: now,
            updated_at: now,
        };
        
        self.apis.insert(id.clone(), api);
        id
    }
    
    pub fn get_api(&self, id: &str) -> Option<&RegisteredApi> {
        self.apis.get(id)
    }
    
    pub fn list_apis(&self) -> Vec<&RegisteredApi> {
        self.apis.values().collect()
    }
    
    pub fn delete_api(&mut self, id: &str) -> bool {
        self.apis.remove(id).is_some()
    }
}
""",
            "api_register_endpoint": """
// src/handlers/api_handlers.rs
use axum::{
    extract::{Json, State},
    http::StatusCode,
    response::Json as JsonResponse,
};
use serde::{Deserialize, Serialize};
use crate::models::api_registry::{ApiRegistry, RegisteredApi};
use crate::openapi::OpenApi30Spec;

#[derive(Debug, Deserialize)]
pub struct RegisterApiRequest {
    pub name: String,
    pub version: String,
    pub spec: String,  // OpenAPI spec content
    pub base_url: String,
}

#[derive(Debug, Serialize)]
pub struct RegisterApiResponse {
    pub success: bool,
    pub api_id: Option<String>,
    pub error: Option<String>,
}

pub async fn register_api(
    State(state): State<AppState>,
    Json(payload): Json<RegisterApiRequest>,
) -> Result<JsonResponse<RegisterApiResponse>, StatusCode> {
    // Parse OpenAPI spec
    let spec = match serde_yaml::from_str::<OpenApi30Spec>(&payload.spec) {
        Ok(spec) => spec,
        Err(_) => {
            // Try JSON parsing
            match serde_json::from_str::<OpenApi30Spec>(&payload.spec) {
                Ok(spec) => spec,
                Err(e) => {
                    return Ok(JsonResponse(RegisterApiResponse {
                        success: false,
                        api_id: None,
                        error: Some(format!("Failed to parse OpenAPI spec: {}", e)),
                    }));
                }
            }
        }
    };
    
    // Register API
    let api_id = state.api_registry.lock().await.register_api(
        payload.name,
        payload.version,
        spec,
        payload.base_url,
    );
    
    Ok(JsonResponse(RegisterApiResponse {
        success: true,
        api_id: Some(api_id),
        error: None,
    }))
}
""",
            "path_matching": """
// src/utils/path_matcher.rs
use std::collections::HashMap;
use regex::Regex;

pub struct PathMatcher {
    path_regex: Regex,
    param_names: Vec<String>,
}

impl PathMatcher {
    pub fn new(path_template: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let mut param_names = Vec::new();
        let mut regex_pattern = path_template.to_string();
        
        // Replace {param} with regex capture groups
        let param_regex = Regex::new(r"\{([^}]+)\}")?;
        regex_pattern = param_regex.replace_all(&regex_pattern, "([^/]+)").to_string();
        
        // Extract parameter names
        for cap in param_regex.captures_iter(path_template) {
            if let Some(param_name) = cap.get(1) {
                param_names.push(param_name.as_str().to_string());
            }
        }
        
        // Add start and end anchors
        regex_pattern = format!("^{}$", regex_pattern);
        
        let path_regex = Regex::new(&regex_pattern)?;
        
        Ok(Self {
            path_regex,
            param_names,
        })
    }
    
    pub fn matches(&self, path: &str) -> bool {
        self.path_regex.is_match(path)
    }
    
    pub fn extract_params(&self, path: &str) -> Option<HashMap<String, String>> {
        let captures = self.path_regex.captures(path)?;
        let mut params = HashMap::new();
        
        for (i, param_name) in self.param_names.iter().enumerate() {
            if let Some(capture) = captures.get(i + 1) {
                params.insert(param_name.clone(), capture.as_str().to_string());
            }
        }
        
        Some(params)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_path_matching() {
        let matcher = PathMatcher::new("/pets/{petId}").unwrap();
        
        assert!(matcher.matches("/pets/123"));
        assert!(!matcher.matches("/pets/123/extra"));
        
        let params = matcher.extract_params("/pets/123").unwrap();
        assert_eq!(params.get("petId"), Some(&"123".to_string()));
    }
}
"""
        }
        
        if task_id in templates:
            print(f"\n📝 {self.tasks[task_id].title} - Rust 代码模板：")
            print("=" * 50)
            print(templates[task_id])
        else:
            print(f"❌ 任务 '{task_id}' 没有可用的代码模板")
    
    def show_help(self):
        """显示帮助信息"""
        print("""
🚀 StepFlow Gateway 开发工具

可用命令：
  show-current    - 显示当前阶段任务
  show-next       - 显示推荐的下一个任务
  show-progress   - 显示项目进度
  update-status <task_id> <status> - 更新任务状态
  generate-code <task_id> - 生成 Rust 代码模板
  help            - 显示此帮助信息

任务状态：
  todo        - 待开始
  in_progress - 进行中
  done        - 已完成

示例：
  python start_development.py show-current
  python start_development.py update-status api_registry_struct in_progress
  python start_development.py generate-code api_registry_struct
        """)

def main():
    planner = DevelopmentPlanner()
    
    if len(sys.argv) < 2:
        planner.show_help()
        return
    
    command = sys.argv[1]
    
    if command == "show-current":
        planner.show_current_phase()
    elif command == "show-next":
        planner.show_next_task()
    elif command == "show-progress":
        planner.show_progress()
    elif command == "update-status" and len(sys.argv) >= 4:
        task_id = sys.argv[2]
        status = sys.argv[3]
        planner.update_task_status(task_id, status)
    elif command == "generate-code" and len(sys.argv) >= 3:
        task_id = sys.argv[2]
        planner.generate_rust_template(task_id)
    elif command == "help":
        planner.show_help()
    else:
        print("❌ 无效命令")
        planner.show_help()

if __name__ == "__main__":
    main() 