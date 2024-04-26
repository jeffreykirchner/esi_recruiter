axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var pixi_app = null;
var pixi_pointer_down = false;        
var pixi_signatures_rope_array = [];
var pixi_signature_texture = null;

var app = Vue.createApp({

    delimiters: ['[[', ']]'],
     
    data() {return{

        waiting:false,
        current_invitation:null,

        consent_form:{{consent_form_json|safe}},
        consent_form_subject:{{consent_form_subject_json|safe}},

        consent_form_error:"",
    }},

    methods:{

        acceptConsentForm:function acceptConsentForm(){

            if(app.consent_form_subject)
            {
                app.consent_form_error = "Refresh the page.";
                return;
            }

            app.consent_form_error = "";

            consent_form_signature = {};
            consent_form_signature_resolution = {};

            if(app.consent_form.signature_required)
            {
                if(pixi_signatures_rope_array.length==0)
                {
                    app.consent_form_error = "Error: Sign before accepting.";
                    return;
                } 
                
                total_length=0;
                for(let i=0;i<pixi_signatures_rope_array.length;i++)
                {
                    consent_form_signature[i]=pixi_signatures_rope_array[i].points;

                    for(let j=1;j<pixi_signatures_rope_array[i].points.length;j++)
                    {
                        let p1 = pixi_signatures_rope_array[i].points[j-1];
                        let p2 = pixi_signatures_rope_array[i].points[j];
                        total_length += app.getDistance(p1.x, p1.y, p2.x, p2.y);
                    }
                }

                if(total_length < 600)
                {
                    app.consent_form_error = "Error: Make your signature larger.";
                    return;
                }

                let canvas = document.getElementById('signature_canvas_id');

                consent_form_signature_resolution['width']=canvas.width;
                consent_form_signature_resolution['height']=canvas.height;
            }

            app.waiting=true;

            axios.post('{{request.get_full_path}}', {
                            action :"acceptConsentForm",        
                            consent_form_id : app.consent_form.id, 
                            consent_form_signature : consent_form_signature, 
                            consent_form_signature_resolution : consent_form_signature_resolution, //{'width':0, 'height':0},                                                                                                                                                      
                        })
                        .then(function (response) {     

                            app.consent_form_subject = response.data.consent_form_subject_json;                                
                            app.waiting=false;
                            
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },

        /**
         * clear signature
         */
        clearSignature: function clearSignature(event){
            if(app.consent_form_subject) return;

            for(i=0;i<pixi_signatures_rope_array.length;i++)
            {
                if(pixi_signatures_rope_array[i].rope) pixi_signatures_rope_array[i].rope.destroy();
                
            }

            pixi_signatures_rope_array = [];
            app.consent_form_error = "";
        },

        getDistance:function getDistance(x1, y1, x2, y2){
            let y = x2 - x1;
            let x = y2 - y1;
            
            return Math.sqrt(x * x + y * y);
        },
        
        handleResize:function handleResize(){      
            if(app.consent_form_subject)
            {
                app.resetPixiApp();
            } 
        },

        {%include "subject/consent_form/pixi_setup.js"%}
  
    },


    mounted(){
        setTimeout(this.resetPixiApp, 500);
        window.addEventListener('resize', this.handleResize);     
    },
}).mount('#app');