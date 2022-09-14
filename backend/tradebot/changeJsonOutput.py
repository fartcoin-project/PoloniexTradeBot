'''{"data":[{"id":3663101,"lstImeis":
    [{"number":"14370340908558","maxDate":"2017-08-24 22:08:58.0","minDate":"2017-08-24 22:08:58.0"},
     {"number":"22418344742097","maxDate":"2017-08-24 18:08:56.0","minDate":"2017-08-24 18:08:56.0"}],
          "number2":789},
         {"id":3665337,"lstImeis":
    [{"number":"48717031235502","maxDate":"2017-08-24 21:09:38.0","minDate":"2017-08-24 21:09:38.0"},
     {"number":"42540009239622","maxDate":"2017-08-24 16:35:08.0","minDate":"2017-08-24 16:35:08.0"},
     {"number":"42540009239644","maxDate":"2017-08-24 16:35:08.0","minDate":"2017-08-24 16:35:08.0"}],
          "number2":456}]}

{"data":[{"id":3663101,
          "number":"14370340908558","maxDate":"2017-08-24 22:08:58.0","minDate":"2017-08-24 22:08:58.0",
          "number2":789},
         {"id":3663101,
          "number":"22418344742097","maxDate":"2017-08-24 18:08:56.0","minDate":"2017-08-24 18:08:56.0",
          "number2":789},
         {"id":3665337,"number":"48717031235502","maxDate":"2017-08-24 21:09:38.0","minDate":"2017-08-24 21:09:38.0",
          "number2":456},
         {"id":3665337,"number":"42540009239622","maxDate":"2017-08-24 16:35:08.0","minDate":"2017-08-24 16:35:08.0",
          "number2":456},
         {"id":3665337,"number":"42540009239644","maxDate":"2017-08-24 16:35:08.0","minDate":"2017-08-24 16:35:08.0",
          "number2":456}]}


var data = new Array();
var str = '{"msg":"success","code":"200","status":null,"data":[{"id":3663101,"lstImeis":[{"number":"14370340908558","maxDate":"2017-08-24 22:08:58.0","minDate":"2017-08-24 22:08:58.0"},{"number":"22418344742097","maxDate":"2017-08-24 18:08:56.0","minDate":"2017-08-24 18:08:56.0"}],"number2":789},{"id":3665337,"lstImeis":[{"number":"48717031235502","maxDate":"2017-08-24 21:09:38.0","minDate":"2017-08-24 21:09:38.0"},{"number":"42540009239622","maxDate":"2017-08-24 16:35:08.0","minDate":"2017-08-24 16:35:08.0"},{"number":"42540009239644","maxDate":"2017-08-24 16:35:08.0","minDate":"2017-08-24 16:35:08.0"}],"number2":456}],"draw":0,"limit":0,"recordsFiltered":0,"recordsTotal":0}';
var response = JSON.parse(str);
var tableData = response.data;
var dataLength = response.data.length;
var finalObj = {data:[]};
for (var i in tableData){
for(var a in tableData[i].lstImeis){
var tmpObj = {};
tmpObj.id = tableData[i].id;
tmpObj.number = tableData[i].lstImeis[a].number;
tmpObj.maxDate = tableData[i].lstImeis[a].maxDate;
tmpObj.minDate = tableData[i].lstImeis[a].minDate;
tmpObj.number2 = tableData[i].number2;
finalObj.data.push(tmpObj);
}
}
alert(JSON.stringify(finalObj));

'''