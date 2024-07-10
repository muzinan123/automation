timeout = 10000;

function formatDate(timestamp){
    date = new Date(timestamp)
    MM = ""+(date.getMonth()+1)
    DD = ""+date.getDate()
    HH = ""+date.getHours()
    mm = ""+date.getMinutes()
    ss = ""+date.getSeconds()
    MM = MM.length==1?"0"+MM:MM
    DD = DD.length==1?"0"+DD:DD
    HH = HH.length==1?"0"+HH:HH
    mm = mm.length==1?"0"+mm:mm
    ss = ss.length==1?"0"+ss:ss
    return date.getFullYear() + "-" + MM + "-" + DD + " " + HH + ":" + mm + ":" + ss
}

function hasChinese(s){
    var patrn=/[\u4E00-\u9FA5]|[\uFE30-\uFFA0]/gi;
    if(!patrn.exec(s)){
        return false;
    }else{
        return true;
    }
}

Vue.filter('bool2str', function (value) {
    if(value){
        return "true";
    }else{
        return "false";
    }
});

Vue.filter('B2MB', function(value){
    if(value){
        return Math.round(value*1/1024/1024)+" MB";
    }else{
        return "-"
    }
});

Vue.filter('get_env_name', function (value) {
    switch(value){
        case 'test':
            return '测试环境'
        case 'pre':
            return '预发环境'
        case 'prd':
            return '生产环境'
        case 'aut':
            return '自动化测试'
    }
});

Vue.filter('obj2str', function(value){
    if(typeof(value)=="object"){
        return JSON.stringify(value)
    }else{
        return value;
    }
});

Vue.filter('get_review_status', function (value) {
    switch(value){
        case 0:
            return '待提交';
        case 1:
            return '已提交';
        case 2:
            return '已评审';
        case 99:
            return '免评审';
    }
});

Vue.filter('get_test_status', function (value) {
    switch(value){
        case 0:
            return '待提交';
        case 1:
            return '测试中';
        case 2:
            return '测试通过';
    }
});

Vue.filter('get_demand_review_status', function (value) {
    switch(value){
        case 0:
            return '未评审';
        case 2:
            return '已评审';
    }
});

Vue.filter('get_publish_status', function (value) {
    switch(value){
        case 0:
            return '待申请发布';
        case 1:
            return '发布中';
        case 2:
            return '已发布';
    }
});

Vue.filter('get_project_type', function (value) {
    switch(value){
        case 'code_optimization':
            return '代码优化'
        case 'system_fault':
            return '系统故障'
        case 'bug_repairs':
            return '缺陷修复'
        case 'requirement_change':
            return '需求变更'
        case 'new_product':
            return '新产品'
        case 'new_feature':
            return '新功能'
        case 'others':
            return '其他'

    }
});

Vue.filter('get_operation_type', function (value) {
    switch(value){
        case 'restart_java_app':
            return '重启Java应用'
        case 'pre_build':
            return '预发打包'
        case 'prd_build':
            return '生产打包'
        case 'init_java_app':
            return '初始化Java应用'
        case 'del_java_app':
            return '删除Java应用'
        case 'archive_log':
            return '归档应用当天日志'
        case 'pre_publish':
            return '预发发布'
        case 'prd_publish':
            return '生产发布'
        case 'commit_project_diamond':
            return '提交Diamond'
        case 'pre_commit':
            return '预发提交代码'
        case 'prd_commit':
            return '生产提交代码'
        case 'dzbd_publish':
            return '电子保单发布'
        case 'pre_dzbd_commit':
            return '预发电子保单提交'
        case 'prd_dzbd_commit':
            return '生产电子保单提交'
        case 'dzbd_rollback':
            return '电子保单回滚'
        case 'pre_precheck':
            return '预发预检'
        case 'prd_precheck':
            return '生产预检'
        case 'local_commit_error':
            return '待预发错误处理'
        case 'nopre_local_commit':
            return '跳过预发流程预发提交'
        case 'pre_diamond_allocate':
            return '分配预发Diamond额度'
        case 'pre_commit_error':
            return '预发提交失败处理'
        case 'prd_diamond_allocate':
            return '分配生产Diamond额度'
        case 'prd_release':
            return '生产发布后释放'
        case 'ci_build':
            return '持续集成打包'
        case 'aut_ci_build':
            return '自动化测试打包'
        case 'release_preallocate_version':
            return '释放项目预占的版本'
        case 'pre_parent_allocate':
            return '准备预发本地Parent'
        case 'wait_app_build':
            return '等待并行打包完成'
        case 'wait_dzbd_publish':
            return '等待电子保单发布完成'
        case 'wait_app_publish':
            return '等待并行发布完成'
        case 'pre_sql_before_execute':
            return '预发发布前执行SQL脚本'
        case 'pre_sql_after_execute':
            return '预发发布后执行SQL脚本'
        case 'prd_sql_before_execute':
            return '生产发布前执行SQL脚本'
        case 'prd_sql_after_execute':
            return '生产发布后执行SQL脚本'
    }
});

Vue.filter('get_role_name', function (value) {
    switch(value){
        case 'qa':
            return '测试'
        case 'dba':
            return 'DBA'
        case 'code_review':
            return '代码审核'
        case 'developer':
            return '开发'
    }
});

Vue.filter('get_process_name', function (value) {
    switch(value){
        case 'PROJECT_SUBMIT':
            return '项目提交'
        case 'PROJECT_ROLLBACK':
            return '项目回撤'
        case 'CODE_REVIEW':
            return 'Code Review'
        case 'SQL_REVIEW':
            return 'SQL Review'
        case 'TEST_VERIFY':
            return '测试验证'
        case 'PUBLISH':
            return '发布'
        case 'PUBLISH_ABANDON':
            return '发布废弃'
        case 'ANTX_REVIEW':
            return 'ANTX评审'
        case 'DIAMOND_REVIEW':
            return 'DIAMOND评审'
    }
});

Vue.filter('get_process_status', function (value) {
    switch(value){
        case 'OWNER_SUBMIT':
            return 'Owner提交'
        case 'OWNER_ROLLBACK':
            return 'Owner撤回'
        case 'CODE_REVIEW_PASS':
            return 'Code Review通过'
        case 'CODE_REVIEW_REJECT':
            return 'Code Review不通过'
        case 'SQL_REVIEW_PASS':
            return 'SQL Review通过'
        case 'SQL_REVIEW_REJECT':
            return 'SQL Review不通过'
        case 'CANCLE_PRE_SQL_EXECUTE':
            return '取消预发SQL脚本执行'
        case 'CANCLE_PRD_SQL_EXECUTE':
            return '取消生产SQL脚本执行'
        case 'TEST_PASS':
            return '测试验证通过'
        case 'TEST_REJECT':
            return '测试验证不通过'
        case 'SUBMIT_TEST_VERIFY':
            return '提交测试验证'
        case 'PUBLISH_NORMAL':
            return '申请常规发布'
        case 'PUBLISH_URGENCY_OTHERS':
            return '紧急发布9-20点'
        case 'PUBLISH_URGENCY_TWENTY_POINTS':
            return '紧急发布20-24点'
        case 'PUBLISH_URGENCY_ZERO_POINTS':
            return '紧急发布0-9点'
        case 'LOCAL_NOT_PASS':
            return 'Owner回退'
        case 'ABANDON':
            return '发布废弃'
        case 'LOCAL_TO_PRE':
            return '自动待预发上预发'
        case 'PRE_SQL_BEFORE_EXECUTED':
            return '预发sql发布前执行'
        case 'PRE_SQL_AFTER_EXECUTED':
            return '预发sql发布后执行'
        case 'PRE_NOT_PASS':
            return '预发验证回退'
        case 'PRE_ROLL_BACK':
            return '预发让步回退'
        case 'NEW_APP_MONITOR':
            return '新应用监控'
        case 'PRE_TO_PRD':
            return '自动预发上生产'
        case 'PRE_PASS':
            return '手动发布至生产'
        case 'PRD_SQL_BEFORE_EXECUTED':
            return '生产sql发布前执行'
        case 'PRD_SQL_AFTER_EXECUTED':
            return '生产sql发布后执行'
        case 'PRD_COMPLETE':
            return '生产自动发布完成'
        case 'ANTX_REVIEW_PASS':
            return 'ANTX评审通过'
        case 'ANTX_REVIEW_REFUSE':
            return 'ANTX评审拒绝'
        case 'DIAMOND_REVIEW_PASS':
            return 'DIAMOND评审通过'
        case 'DIAMOND_REVIEW_REFUSE':
            return 'DIAMOND评审拒绝'
    }
});

Vue.filter('get_rollback_name', function (value) {
    switch(value){
        case 'owner_rollback_reason':
            return '项目owner自主回退'
        case 'pre_not_pass_reason':
            return '预发验证回退'
    }
});

Vue.filter('get_rollback_reason', function (value) {
    switch(value){
        case 'exist_bug':
            return '存在Bug'
        case 'publish_problem':
            return '发布问题'
        case 'commit_problem':
            return '代码漏提交'
        case 'code_conflict':
            return '代码冲突'
        case 'code_stale':
            return '不是最新代码'
        case 'other':
            return '其他'
    }
});

Vue.filter('get_weekday', function (value) {
    switch(value){
        case "1":
            return '星期一'
        case "2":
            return '星期二'
        case "3":
            return '星期三'
        case "4":
            return '星期四'
        case "5":
            return '星期五'
        case "6":
            return '星期六'
        case "7":
            return '星期天'
    }
});

Vue.filter('sql_review_status', function(value){
     switch(value){
        case "init":
            return '待提交'
        case "review":
            return "审核中"
        case "pass":
            return "通过"
        case "not_pass":
            return "未通过"
        case "execute":
            return "执行中"
        case "success":
            return "执行成功"
        case "failed":
            return "执行失败"
      }
});