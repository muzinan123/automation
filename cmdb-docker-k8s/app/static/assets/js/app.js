timeout = 10000;

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
            return '测试'
        case 'pre':
            return '预发'
        case 'prd':
            return '生产'
    }
});

Vue.filter('get_org_name', function (value) {
    switch(value){
        case 'ZA':
            return '众安保险'
        case 'ZATECH':
            return '众安科技'
        case 'BAOYUN':
            return '豹云'
        case 'YIYUAN':
            return '宜员'
        case 'WX':
            return '威寻'
        case 'ZAZJ':
            return '众安经纪'
        case 'XD':
            return '众安小贷'
        case 'NUANWA':
            return '暖哇'
        case 'FENGDIAN':
            return '蜂点'
        case 'ZAINTL':
            return '众安国际'
    }
});
