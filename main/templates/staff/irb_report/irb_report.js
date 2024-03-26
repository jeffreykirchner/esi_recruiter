{% load static %}

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({

    delimiters: ['[[', ']]'],     

    data() {return{               

        working:false,
        irb_report:null,
        form_ids:{{form_ids|safe}},
        start_range:"{{d_fisical_start}}",
        end_range:"{{d_today}}",

    }},

    methods:{
        
        //get list of open experiments
        getIrbForm:function(){       

            app.$data.working=true;
            app.clearMainFormErrors();

            axios.post('{{ request.path }}', {
                        action :"getIrbForm" ,   
                        formData : $("#irbReportForm").serializeArray(),                                                                                                                          
                        })
                        .then(function (response) {     

                            status=response.data.status;                                                                  
                            app.$data.working=false;

                            if(status=="fail")
                            {                         
                                app.displayErrors(response.data.errors);             
                            }
                            else
                            {                            
                                app.$data.irb_report = response.data.irb_report;
                            }
                            
                            
                        })
                        .catch(function (error) {
                            console.log(error);                            
                        });                        
        },

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
                
                s = app.$data.form_ids;
                for(var i in s)
                {
                    $("#id_" + s[i]).attr("class","form-control");
                    $("#id_errors_" + s[i]).remove();
                }
            },

      
    
    },
        
    mounted(){
                      
    },
    
}).mount('#app');