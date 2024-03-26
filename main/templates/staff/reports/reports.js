axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({

    delimiters: ['[[', ']]'],
   
    data(){return{
        pettyCash:{
                    department:"",
                    startDate:"",
                    endDate:"",
                    department_name:"",
                    },
        studentReport:{
                    studentReport_gt600:0,
                    studentReport_studentWorkers:0,
                    studentReport_nra:0,
                    studentReport_department_or_account:"Department",
                    studentReport_outside_funding:-1,
                    studentReport_include_archived:0,
                    studentReport_startDate:'{{d_fisical_start}}',
                    studentReport_endDate:'{{d_today}}',                
        },
        maxAnnualEarnings:{{maxAnnualEarnings}},
        pettyCashButtonText:'Generate <i class="fas fa-scroll fa-xs"></i>',
        studentReportButtonText:'Generate <i class="fas fa-scroll fa-xs"></i>',

    }},

    methods:{
        //display form errors
        displayErrors:function(errors){
                for(var e in errors)
                {
                    $("#id_" + e).attr("class","form-control is-invalid")
                    var str='<span id=id_errors_'+ e +' class="text-danger">';
                    
                    for(var i in errors[e])
                    {
                        str +=errors[e][i] + '<br>';
                    }

                    str+='</span>';
                    $("#div_id_" + e).append(str);    

                    var elmnt = document.getElementById("div_id_" + e);
                    elmnt.scrollIntoView(); 
                }
            },

        //clear errors from forms
        clearMainFormErrors:function(){
                for(var item in app.$data.pettyCash)
                {
                    $("#id_" + item).attr("class","form-control");
                    $("#id_errors_" + item).remove();
                }  
                
                for(var item in app.$data.studentReport)
                {
                    $("#id_" + item).attr("class","form-control");
                    $("#id_errors_" + item).remove();
                }
            },

        //get the petty chash csv
        getPettyCash:function(){
            app.$data.pettyCashButtonText='<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/reports/', {
                            action :"getPettyCash" ,
                            formData : $("#pettyCashForm").serializeArray(),                                                                                                                             
                        })
                        .then(function (response) { 
                            status=response.data.status;                                                                  

                            app.clearMainFormErrors();

                            if(status=="fail")
                            {                         
                                app.displayErrors(response.data.errors);             
                            }
                            else
                            {                                                                       
                                console.log(response.data);

                                var downloadLink = document.createElement("a");
                                var blob = new Blob(["\ufeff", response.data]);
                                var url = URL.createObjectURL(blob);
                                downloadLink.href = url;
                                downloadLink.download = "Petty_Cash_" + $( "#id_department option:selected" ).text() + "_"+ app.$data.pettyCash.startDate + "_to_" + app.$data.pettyCash.endDate + ".csv";

                                document.body.appendChild(downloadLink);
                                downloadLink.click();
                                document.body.removeChild(downloadLink);
                            }    
                            
                            app.$data.pettyCashButtonText = 'Generate <i class="fas fa-scroll fa-xs"></i>';
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.$data.searching=false;
                        });                        
                    },

        //get the petty chash csv
        getStudentReport:function(){
            app.$data.studentReportButtonText='<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/reports/', {
                            action :"getStudentReport" ,
                            formData : $("#studentReportForm").serializeArray(),                                                                                                                             
                        })
                        .then(function (response) { 
                            status=response.data.status;                                                                  

                            app.clearMainFormErrors();

                            if(status=="fail")
                            {                         
                                app.displayErrors(response.data.errors);             
                            }
                            else
                            {                                                                       
                                console.log(response.data);

                                var downloadLink = document.createElement("a");
                                var blob = new Blob(["\ufeff", response.data]);
                                var url = URL.createObjectURL(blob);
                                downloadLink.href = url;
                                downloadLink.download = "Student_Report_" + app.$data.studentReport.studentReport_startDate + "_to_"+ app.$data.studentReport.studentReport_endDate + ".csv";

                                document.body.appendChild(downloadLink);
                                downloadLink.click();
                                document.body.removeChild(downloadLink);
                            }    
                            
                            app.$data.studentReportButtonText = 'Generate <i class="fas fa-scroll fa-xs"></i>';
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.$data.searching=false;
                        });                        
                    },
    },

    mounted(){
                                
    },
}).mount('#app');