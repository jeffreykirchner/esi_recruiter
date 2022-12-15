axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({

    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{

        waiting:false,
        current_invitation:null,

        consent_form:{{consent_form_json|safe}},
        consent_form_subject:{{consent_form_subject_json|safe}},

        pixi_app:null,
        pixi_pointer_down:false,        
        pixi_signatures_rope_array:[],
        pixi_signature_texture:null,

        consent_form_error:"",
    },

    methods:{

        acceptConsentForm:function(){

            if(app.$data.consent_form_subject)
            {
                app.$data.consent_form_error = "Refresh the page.";
                return;
            }

            app.$data.consent_form_error = "";

            consent_form_signature = {};
            consent_form_signature_resolution = {};

            if(app.$data.consent_form.signature_required)
            {
                if(app.$data.pixi_signatures_rope_array.length==0)
                {
                    app.$data.consent_form_error = "Error: Sign before accepting.";
                    return;
                } 
                
                total_length=0;
                for(let i=0;i<app.$data.pixi_signatures_rope_array.length;i++)
                {
                    consent_form_signature[i]=app.$data.pixi_signatures_rope_array[i].points;

                    for(let j=1;j<app.$data.pixi_signatures_rope_array[i].points.length;j++)
                    {
                        let p1 = app.$data.pixi_signatures_rope_array[i].points[j-1];
                        let p2 = app.$data.pixi_signatures_rope_array[i].points[j];
                        total_length += app.getDistance(p1.x, p1.y, p2.x, p2.y);
                    }
                }

                if(total_length < 600)
                {
                    app.$data.consent_form_error = "Error: Make your signature larger.";
                    return;
                }

                let canvas = document.getElementById('signature_canvas_id');

                consent_form_signature_resolution['width']=canvas.width;
                consent_form_signature_resolution['height']=canvas.height;
            }

            app.$data.waiting=true;

            axios.post('{{request.get_full_path}}', {
                            action :"acceptConsentForm",        
                            consent_form_id : app.$data.consent_form.id, 
                            consent_form_signature : consent_form_signature, 
                            consent_form_signature_resolution : consent_form_signature_resolution, //{'width':0, 'height':0},                                                                                                                                                      
                        })
                        .then(function (response) {     

                            app.$data.consent_form_subject = response.data.consent_form_subject_json;                                
                            app.$data.waiting=false;
                            
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },

        /**
         * clear signature
         */
        clearSignature(event){
            if(app.consent_form_subject) return;

            for(i=0;i<app.$data.pixi_signatures_rope_array.length;i++)
            {
                if(app.$data.pixi_signatures_rope_array[i].rope) app.$data.pixi_signatures_rope_array[i].rope.destroy();
                
            }

            app.$data.pixi_signatures_rope_array = [];
            app.$data.consent_form_error = "";
        },

        getDistance:function(x1, y1, x2, y2){
            let y = x2 - x1;
            let x = y2 - y1;
            
            return Math.sqrt(x * x + y * y);
        },
        
        handleResize:function(){      
            if(app.$data.consent_form_subject)
            {
                app.resetPixiApp();
            } 
        },

        {%include "subject/consent_form/pixi_setup.js"%}
  
    },


    mounted: function(){
        setTimeout(this.resetPixiApp, 500);
        window.addEventListener('resize', this.handleResize);     
    },
});