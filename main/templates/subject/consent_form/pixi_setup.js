{% load static %}

/**
 * update the pixi players with new info
 */
setupPixi(){    
    app.resetPixiApp();
},

resetPixiApp(){
    
    let canvas = document.getElementById('signature_canvas_id');

    if(!app.$data.pixi_app)
    {
        app.$data.pixi_app = new PIXI.Application({resizeTo : canvas,
                                                backgroundColor : 0xFFFFFF,
                                                autoResize: true,
                                                antialias: true,
                                                resolution: 1,
                                                view: canvas });
    }
    
    app.$data.pixi_signature_texture = PIXI.Texture.from('{% static "signature_4.png" %}');

    app.$data.canvas_width = canvas.width;
    app.$data.canvas_height = canvas.height;

    //add background rectangle
    let background = new PIXI.Graphics();
    background.beginFill(0xf8f8ff);
    background.drawRect(0, 0, canvas.width, canvas.height);
    background.endFill();

    background.interactive = true;
    background.on("pointerdown", app.handleStagePointerDown)
              .on("pointerup", app.handleStagePointerUp)              
              .on("pointermove", app.handleStagePointerMove);
    app.$data.pixi_app.stage.addChild(background);

    //add signature line
    let signature_line = new PIXI.Graphics();
    signature_line.lineStyle(2, 0xDCDCDC)
                  .moveTo(5, canvas.height*0.75)                    //horizontal line
                  .lineTo(canvas.width-10, canvas.height*0.75)
                  .moveTo(5, canvas.height*0.65)                    //x   
                  .lineTo(15, canvas.height*0.74)
                  .moveTo(15, canvas.height*0.65)                     
                  .lineTo(5, canvas.height*0.74);

    app.$data.pixi_app.stage.addChild(signature_line);

    //sign here text
    let text = "";
    if(app.consent_form && app.consent_form.signature_required)
    {
        text = new PIXI.Text('Sign Here',{fontFamily : 'Arial', fontSize: 24, fill : 0xDCDCDC, align : 'center'});
    }
    else
    {
        text = new PIXI.Text('No Signature Required',{fontFamily : 'Arial', fontSize: 24, fill : 0xDC143C, align : 'center'});
    }
    text.x = canvas.width/2-text.width/2;
    text.y = canvas.height*0.74-text.height;
    app.$data.pixi_app.stage.addChild(text);

    //animation ticker
    app.$data.pixi_app.ticker.add((delta) => {               
        app.pixiTicker(delta)
    });

    //load signature
    app.loadSignature();
},

//load past signature
loadSignature(){

    app.$data.pixi_signatures_rope_array = [];

    if(!app.consent_form) return;
    if(!app.consent_form.signature_required) return;
    if(!app.consent_form_subject) return;

    
    let s = app.consent_form_subject.singnature_resolution;

    if(!s)
    {
         s={width:app.$data.canvas_width,height:app.$data.canvas_height};
    }
    // else
    // {
    //     s.width=app.$data.canvas_width/s.width;
    //     s.height=app.$data.canvas_height/s.height;
    // }

    for (let i in app.consent_form_subject.signature_points) {

        let t = app.consent_form_subject.signature_points[i];        

        let points = [];

        for(let j=0;j<t.length;j++)
        {
            points.push(new PIXI.Point(t[j].x * app.$data.canvas_width / s.width,
                                       t[j].y * app.$data.canvas_height / s.height))
        }

        v = {points:points, rope:new PIXI.SimpleRope(app.$data.pixi_signature_texture, new PIXI.Point(0, 0))};
            
       //v.rope.blendmode = PIXI.BLEND_MODES.ADD;    
       app.$data.pixi_signatures_rope_array.push(v);
    }
},

pixiTicker(delta){
    for(i=0;i<app.$data.pixi_signatures_rope_array.length;i++)
    {
        if(app.$data.pixi_signatures_rope_array[i].points.length > 0)
        {
            if(app.$data.pixi_signatures_rope_array[i].rope) app.$data.pixi_signatures_rope_array[i].rope.destroy();
            
            app.$data.pixi_signatures_rope_array[i].rope = new PIXI.SimpleRope(app.$data.pixi_signature_texture,
                                                                               app.$data.pixi_signatures_rope_array[i].points,
                                                                               start=0,
                                                                            );
                                                                            
            app.$data.pixi_app.stage.addChild(app.$data.pixi_signatures_rope_array[i].rope);
        }
    }
},

/**
 *pointer up on stage
*/
handleStagePointerDown(event){

    if(app.consent_form_subject) return;
    if(app.waiting) return;

    app.$data.pixi_pointer_down=true;
    v = {points:[new PIXI.Point(event.data.global.x, event.data.global.y)], rope: null};
        
    //v.rope.blendmode = PIXI.BLEND_MODES.ADD;    
    app.$data.pixi_signatures_rope_array.push(v);
},

/**
 *pointer up on stage
 */
handleStagePointerUp(){
    app.$data.pixi_pointer_down=false;    
},

/**
 * pointer move over stage
 */
handleStagePointerMove(event){
    if(app.waiting) return;
    if(!app.$data.pixi_pointer_down) return;

    let i = app.$data.pixi_signatures_rope_array.length-1;

    if(i<0)i=0;

    app.$data.pixi_signatures_rope_array[i].points.push(new PIXI.Point(event.data.global.x, event.data.global.y));    
},