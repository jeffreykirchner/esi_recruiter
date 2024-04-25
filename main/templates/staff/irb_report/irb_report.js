{% load static %}

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({

    delimiters: ['[[', ']]'],     

    data() {return{               

        working:false,
        irb_report:null,
        form_ids:{{form_ids|safe}},
        
        irb_report_form:{start_range:"{{d_fisical_start}}",
                         end_range:"{{d_today}}",
                         irb_study:null,
        },

    }},

    methods:{
        
        //get list of open experiments
        getIrbForm:function getIrbForm(){       

            app.working=true;
            app.clearMainFormErrors();

            axios.post('{{ request.path }}', {
                        action :"getIrbForm" ,   
                        formData : app.irb_report_form,                                                                                                                          
                        })
                        .then(function (response) {     

                            status=response.data.status;                                                                  
                            app.working=false;

                            if(status=="fail")
                            {                         
                                app.displayErrors(response.data.errors);             
                            }
                            else
                            {                            
                                app.irb_report = response.data.irb_report;
                            }
                        })
                        .catch(function (error) {
                            console.log(error);                            
                        });                        
        },

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
        clearMainFormErrors:function clearMainFormErrors(){
                
                s = app.form_ids;
                for(var i in s)
                {
                    let e = document.getElementById("id_errors_" + s[i]);
                    if(e) e.remove();
                }
            },

      
    
    },
        
    mounted(){
                      
    },
    
}).mount('#app');