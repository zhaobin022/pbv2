(function (jq) {
    function  getChoiceName(job_type_id,key) {
        var ret = '';
        $.each(GLOBAL_CHOICE,function (k,v) {
            $.each(v[key],function (kk,vv) {
                if (vv[0]==job_type_id) {
                     ret = vv[1];
                };
            });

        });
        return ret;
    };

    function getConstant(k) {
        return CONSTANT_DICT[k];
    }

    function initTableHead(ret) {
       var tr = document.createComment('tr');

        $.each(ret.table_config,function (k,v) {
            if(v.display){
                var th = document.createElement('th');
                th.innerHTML = v.title;
                $('thead').append(th);
            }

        });
        $('thead').append(tr);

    };

    function initTableBody(ret){
        $.each(ret.data_list,function (k,row) {
            var tr = document.createElement('tr');
            $.each(ret.table_config,function (k,conf) {
                if (conf.display) {
                    var td = document.createElement('td');
                    var content = '';
                    var kwargs_dict = {};
                    if (conf.text){
                        $.each(conf.text.kwargs,function (kwargs_key,kwargs_value) {
                             if(kwargs_value.substring(0,3) == "@@@") {
                                 var key = kwargs_value.substring(3,kwargs_value.length);
                                 kwargs_dict[kwargs_key] = getConstant(key);

                             } else if(kwargs_value.substring(0,2) == "@@") {
                                 var key = kwargs_value.substring(2,kwargs_value.length);

                                 kwargs_dict[kwargs_key] = getChoiceName(row[conf.q],key);

                             } else if(kwargs_value.substring(0,1) == "@") {
                                  var key = kwargs_value.substring(1,kwargs_value.length);
                                  kwargs_dict[kwargs_key] = row[key];
                             };
                        });

                        content = conf.text.tpl.format(kwargs_dict);
                    } else {
                        content = row[conf.q];

                    };
                    $(td).html(content);
                    $(tr).append(td);
                };
             });
            $('tbody').append(tr);
        });
    };

    function  initPage(ret) {
        $('#page_content').html(ret.page_content);
    };

    function  getSearch() {
        var result = {};
        $('#search').find('input[type="text"],select').each(function(){
            var name = $(this).attr('name');
            var val = $(this).val();
            result[name] = val
        });
        return result;
    };

    function emptyTable(){
        $('thead').empty();
        $('tbody').empty();
        $('page_content').empty();

    };

    function bindSearch(ret) {
         if (SEARCH_BIND_TAG){
            $.each(ret.search_config,function(k,v) {
               if (v.mode == 'global' ){
                   if (v.bind == 'change') {
                       $('#'+v.id).on('input propertychange', function() {
                            initTable(1);
                        });
                       $('#'+v.id).prop("placeholder",v.placeholder);
                   };
               };
            });
            SEARCH_BIND_TAG = false;
         };

    };

    function  bindPageElements() {
        $("body").on("click", "[page]", function() {
            var page = $(this).attr("page");
            initTable(page);
        });

    };

    function bindEvents() {
        bindPageElements();
    };

    function initTable(page){
       <!-- init table -->
        $('#loading').removeClass('hide');
        emptyTable();
        var data = {}
        var search_content = getSearch();
        if (search_content){
            data['search'] = JSON.stringify(search_content);
        };

        data['page'] = page;
        $.ajax({
            url:requestUrl,
            type: 'GET',
            data: data,
            dataType: 'JSON',
            success:function (response) {

                GLOBAL_CHOICE = response.global_choices_dict;

                CONSTANT_DICT =  response.constant_dict;
                /* 处理表头 */
                initTableHead(response);
                /* 处理表内容 */
                initTableBody(response);

                initPage(response);

                bindSearch(response);
                $('#loading').addClass('hide');
            },
            error:function () {
                $('#loading').addClass('hide');
            }
        });
    };

    String.prototype.format = function (args) {
        return this.replace(/\{(\w+)\}/g, function (s, i) {
            return args[i];
        });
    };

    jq.extend({
        "ajaxList":function (url) {
            requestUrl = url;
            SEARCH_BIND_TAG = true;
            initTable(1);
            bindEvents();
        },
    });
})(jQuery);