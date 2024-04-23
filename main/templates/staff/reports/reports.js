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
        displayErrors: function displayErrors(errors){
            for(let e in errors)
            {
                let str='<span id=id_errors_'+ e +' class="text-danger">';
                
                for(let i in errors[e])
                {
                    str +=errors[e][i] + '<br>';
                }

                str+='</span>';

                document.getElementById("div_id_" + e).insertAdjacentHTML('beforeend', str);
                //scroll to the last error
                var elmnt =  document.getElementById("div_id_" + e);
                if(elmnt) elmnt.scrollIntoView();
            }
        }, 

        //clear errors from forms
        clearMainFormErrors:function(){
                for(var item in app.pettyCash)
                {
                    let e = document.getElementById("id_errors_" + item);
                    if(e) e.remove();
                }  
                
                for(var item in app.studentReport)
                {
                    let e = document.getElementById("id_errors_" + item);
                    if(e) e.remove();
                }
            },

        //get the petty chash csv
        getPettyCash:function(){
            app.pettyCashButtonText='<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/reports/', {
                            action :"getPettyCash" ,
                            formData : app.pettyCash,                                                                                                                             
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
                                var e = document.getElementById("id_department");
                                var value = e.options[e.selectedIndex].value;
                                var text = e.options[e.selectedIndex].text;
                                downloadLink.download = "Petty_Cash_" + text + "_"+ app.pettyCash.startDate + "_to_" + app.pettyCash.endDate + ".csv";

                                document.body.appendChild(downloadLink);
                                downloadLink.click();
                                document.body.removeChild(downloadLink);
                            }    
                            
                            app.pettyCashButtonText = 'Generate <i class="fas fa-scroll fa-xs"></i>';
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.searching=false;
                        });                        
                    },

        //get the petty chash csv
        getStudentReport:function(){
            app.studentReportButtonText='<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/reports/', {
                            action :"getStudentReport" ,
                            formData : app.studentReport,                                                                                                                             
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
                                downloadLink.download = "Student_Report_" + app.studentReport.studentReport_startDate + "_to_"+ app.studentReport.studentReport_endDate + ".csv";

                                document.body.appendChild(downloadLink);
                                downloadLink.click();
                                document.body.removeChild(downloadLink);
                            }    
                            
                            app.studentReportButtonText = 'Generate <i class="fas fa-scroll fa-xs"></i>';
                        })
                        .catch(function (error) {
                            console.log(error);
                            app.searching=false;
                        });                        
                    },
    },

    mounted(){
                                
    },
}).mount('#app');