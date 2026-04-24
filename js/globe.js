var s1=document.createElement('script');
s1.src='https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
s1.onload=function(){
  var s2=document.createElement('script');
  s2.src='https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js';
  s2.onload=function(){startGlobe();};
  document.head.appendChild(s2);
};
document.head.appendChild(s1);

function startGlobe(){
  var gw=document.getElementById('gw');
  var cardBox=document.getElementById('card-box');
  var rect=gw.getBoundingClientRect();
  var GS=Math.round(rect.width);

  var scene=new THREE.Scene();
  var camera=new THREE.PerspectiveCamera(45,1,0.1,1000);
  camera.position.set(0,0,3.0);
  var renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
  renderer.setSize(GS,GS);renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setClearColor(0x000000,0);renderer.domElement.style.cursor='pointer';
  gw.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xc8c8e0,0.6));
  var dl=new THREE.DirectionalLight(0xfff8f0,0.48);dl.position.set(-2,1.5,3);scene.add(dl);
  var fl=new THREE.DirectionalLight(0x8090b0,0.15);fl.position.set(2,-0.5,-1);scene.add(fl);

  var txW=8192,txH=4096,txCv=document.createElement('canvas');txCv.width=txW;txCv.height=txH;
  var tx=txCv.getContext('2d');
  var og=tx.createLinearGradient(0,0,0,txH);
  og.addColorStop(0,'#1a3a6e');og.addColorStop(0.25,'#224e92');og.addColorStop(0.5,'#2d60a8');og.addColorStop(0.75,'#224e92');og.addColorStop(1,'#1a3a6e');
  tx.fillStyle=og;tx.fillRect(0,0,txW,txH);
  tx.strokeStyle='rgba(255,255,255,0.018)';tx.lineWidth=0.5;
  for(var i=-75;i<=75;i+=15){var y=txH/2-i/180*txH;tx.beginPath();tx.moveTo(0,y);tx.lineTo(txW,y);tx.stroke();}
  for(var i=-180;i<=180;i+=15){var x=(i+180)/360*txW;tx.beginPath();tx.moveTo(x,0);tx.lineTo(x,txH);tx.stroke();}

  var earthTex=new THREE.CanvasTexture(txCv);
  fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/land-10m.json').then(function(r){return r.json();}).then(function(world){
    var land=topojson.feature(world,world.objects.land);
    land.features.forEach(function(f){
      var dr=function(ring){tx.beginPath();ring.forEach(function(c,i){var px=(c[0]+180)/360*txW;var py=(90-c[1])/180*txH;i===0?tx.moveTo(px,py):tx.lineTo(px,py);});tx.closePath();tx.fillStyle='#ece8e2';tx.fill();tx.strokeStyle='rgba(200,195,185,0.35)';tx.lineWidth=1.0;tx.stroke();};
      if(f.geometry.type==='Polygon')f.geometry.coordinates.forEach(function(r){dr(r);});
      else if(f.geometry.type==='MultiPolygon')f.geometry.coordinates.forEach(function(p){p.forEach(function(r){dr(r);});});
    });
    earthTex.needsUpdate=true;
  });

  var earthGroup=new THREE.Group();scene.add(earthGroup);
  var earth=new THREE.Mesh(new THREE.SphereGeometry(1,128,128),new THREE.MeshPhongMaterial({map:earthTex,specular:0x3060a0,shininess:6,emissive:0x080e1a,emissiveIntensity:0.06}));
  earthGroup.add(earth);
  earthGroup.add(new THREE.Mesh(new THREE.SphereGeometry(1.04,64,64),new THREE.ShaderMaterial({vertexShader:'varying vec3 vN;void main(){vN=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',fragmentShader:'varying vec3 vN;void main(){float i=pow(0.58-dot(vN,vec3(0,0,1)),3.0);gl_FragColor=vec4(0.3,0.5,0.85,1.0)*i*0.6;}',blending:THREE.AdditiveBlending,side:THREE.BackSide,transparent:true})));
  earthGroup.add(new THREE.Mesh(new THREE.SphereGeometry(1.10,64,64),new THREE.ShaderMaterial({vertexShader:'varying vec3 vN;void main(){vN=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',fragmentShader:'varying vec3 vN;void main(){float i=pow(0.4-dot(vN,vec3(0,0,1)),2.0);gl_FragColor=vec4(0.35,0.55,0.88,1.0)*i*0.18;}',blending:THREE.AdditiveBlending,side:THREE.BackSide,transparent:true})));

  // Locations: India, St. Louis, DC, Barcelona, Singapore
  var locs=[
    {name:'Karnataka, India',lat:15.3,lng:75.1,col:0x8B5CF6,hex:'139,92,246',tag:'WHERE IT STARTED',tagBg:'#f0eeff',tagCol:'#6D28D9',proj:'Medical Officer \u00b7 Integrative Practice',desc:'Practiced as an integrative healthcare professional in primary care and community health. Redesigned clinic EHR workflows and led public health outreach. Founded an 800+ member mentoring community for naturopathy graduates.'},
    {name:'St. Louis, USA',lat:38.63,lng:-90.20,col:0x6366F1,hex:'99,102,241',tag:'HOME BASE',tagBg:'#eef2ff',tagCol:'#4338CA',proj:'Dual MPH/MBA \u00b7 Researcher \u00b7 Product Builder',desc:'WashU Olin Business School & School of Public Health. Product lead for Nyrocare. Cancer epidemiology at Siteman Cancer Center. Stats Lab analyst. Madera Hospital turnaround strategy.'},
    {name:'Washington DC, USA',lat:38.91,lng:-77.04,col:0x3B82F6,hex:'59,130,246',tag:'GLOBAL IMMERSION',tagBg:'#eff6ff',tagCol:'#2563EB',proj:'Policy & Institutions',desc:'Collaborated with Brookings Institution scholars on remote work productivity and public policy analysis.'},
    {name:'Barcelona, Spain',lat:41.39,lng:2.17,col:0xF472B6,hex:'244,114,182',tag:'GLOBAL IMMERSION',tagBg:'#fdf2f8',tagCol:'#DB2777',proj:'Market Entry Strategy',desc:'Developed a full market entry plan for a US food business expanding to Spain. Site selection, competitor analysis, consumer focus groups, and financial projection.'},
    {name:'Singapore',lat:1.35,lng:103.82,col:0x10B981,hex:'16,185,129',tag:'GLOBAL IMMERSION',tagBg:'#ecfdf5',tagCol:'#059669',proj:'Global Operations Strategy',desc:'Partnered with Emerson Electric on global distribution network resilience and supply chain optimization across Asia-Pacific.'}
  ];

  function ll2v(lat,lng,r){var phi=(90-lat)*(Math.PI/180),theta=(lng+180)*(Math.PI/180);return new THREE.Vector3(-r*Math.sin(phi)*Math.cos(theta),r*Math.cos(phi),r*Math.sin(phi)*Math.sin(theta));}
  function getTargetRotY(lng){return -(lng+90)*(Math.PI/180);}
  function getTargetRotX(lat){return lat*(Math.PI/180)*0.35;}

  // FIX 3: Great circle arc with slerp + distance-based height
  function greatCircleArc(fromIdx,toIdx,nPts){
    var v1=ll2v(locs[fromIdx].lat,locs[fromIdx].lng,1).normalize();
    var v2=ll2v(locs[toIdx].lat,locs[toIdx].lng,1).normalize();
    var angle=Math.acos(Math.max(-1,Math.min(1,v1.dot(v2))));
    var sinA=Math.sin(angle);
    var peakH=angle*0.15;
    var pts=[];
    for(var i=0;i<=nPts;i++){
      var t=i/nPts;
      var w1=sinA>0.001?Math.sin((1-t)*angle)/sinA:1-t;
      var w2=sinA>0.001?Math.sin(t*angle)/sinA:t;
      var p=new THREE.Vector3(v1.x*w1+v2.x*w2,v1.y*w1+v2.y*w2,v1.z*w1+v2.z*w2);
      p.normalize();
      var h=1.02+peakH*Math.sin(t*Math.PI);
      p.multiplyScalar(h);
      pts.push(p);
    }
    return pts;
  }

  // Store marker meshes for raycasting + rings for smooth highlight
  var markerMeshes=[];
  var markerRings=[];
  locs.forEach(function(loc,idx){
    var pos=ll2v(loc.lat,loc.lng,1.02);
    var dot=new THREE.Mesh(new THREE.SphereGeometry(0.035,16,16),new THREE.MeshBasicMaterial({color:loc.col,transparent:true,opacity:0.35}));dot.position.copy(pos);dot.userData.locIdx=idx;earth.add(dot);
    markerMeshes.push(dot);
    var ctr=new THREE.Mesh(new THREE.SphereGeometry(0.014,12,12),new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:0.9}));ctr.position.copy(pos);earth.add(ctr);
    var ring=new THREE.Mesh(new THREE.RingGeometry(0.04,0.058,32),new THREE.MeshBasicMaterial({color:loc.col,transparent:true,opacity:0.08,side:THREE.DoubleSide}));ring.position.copy(pos);ring.lookAt(new THREE.Vector3(0,0,0));earth.add(ring);
    markerRings.push(ring);
  });

  // Permanent arc connections - complete loop, always visible, pink
  [[0,1],[1,2],[2,3],[3,4],[4,0]].forEach(function(pair){
    var pts=greatCircleArc(pair[0],pair[1],80);
    earth.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:0xF472B6,transparent:true,opacity:0.7})));
  });

  // ===== FLIGHT PATH (pink arc line + magenta arrowhead) =====
  var flightPts=60;
  var flightGeom=new THREE.BufferGeometry();
  var flightPositions=new Float32Array((flightPts+1)*3);
  flightGeom.setAttribute('position',new THREE.BufferAttribute(flightPositions,3));
  flightGeom.setDrawRange(0,0);
  // FIX 1: Pink flight line
  var flightMat=new THREE.LineBasicMaterial({color:0xF472B6,transparent:true,opacity:0.8,depthWrite:false});
  var flightLine=new THREE.Line(flightGeom,flightMat);
  flightLine.visible=false;
  earthGroup.add(flightLine);

  // Flat 2D airplane silhouette (top-down view)
  var planeShape=new THREE.Shape();
  // Nose
  planeShape.moveTo(0,0.024);
  // Right fuselage to wing
  planeShape.lineTo(0.003,0.012);
  // Right wing tip
  planeShape.lineTo(0.022,0.004);
  planeShape.lineTo(0.022,0.001);
  // Right fuselage after wing
  planeShape.lineTo(0.003,-0.002);
  // Right tail
  planeShape.lineTo(0.012,-0.018);
  planeShape.lineTo(0.012,-0.022);
  // Tail center
  planeShape.lineTo(0.002,-0.016);
  planeShape.lineTo(0,-0.018);
  // Left tail
  planeShape.lineTo(-0.002,-0.016);
  planeShape.lineTo(-0.012,-0.022);
  planeShape.lineTo(-0.012,-0.018);
  // Left fuselage after wing
  planeShape.lineTo(-0.003,-0.002);
  // Left wing tip
  planeShape.lineTo(-0.022,0.001);
  planeShape.lineTo(-0.022,0.004);
  // Left fuselage to nose
  planeShape.lineTo(-0.003,0.012);
  planeShape.lineTo(0,0.024);
  var planeGeom=new THREE.ShapeGeometry(planeShape);
  var planeMat=new THREE.MeshBasicMaterial({color:0xF472B6,transparent:true,opacity:1.0,side:THREE.DoubleSide,depthWrite:false});
  var planeMesh=new THREE.Mesh(planeGeom,planeMat);
  var planeGroup=new THREE.Group();
  planeGroup.add(planeMesh);
  // Soft glow behind the plane
  var planeGlow=new THREE.Mesh(new THREE.CircleGeometry(0.018,16),new THREE.MeshBasicMaterial({color:0xEC4899,transparent:true,opacity:0.3,side:THREE.DoubleSide,depthWrite:false}));
  planeGroup.add(planeGlow);
  planeGroup.visible=false;
  earthGroup.add(planeGroup);
  var arrowMesh=planeGroup;
  var arrowMat=planeMat;
  var prevPlaneQuat=new THREE.Quaternion();

  var flightArcPts=null;
  var flightInitialDiff=1;
  var flightFadeout=-1;

  function startFlight(fromIdx,toIdx){
    // FIX 3: Great circle flight path
    flightArcPts=greatCircleArc(fromIdx,toIdx,flightPts);
    var dy=tRY-curRY;
    // FIX 2: Use actual signed delta (shortest path)
    while(dy>Math.PI)dy-=Math.PI*2;
    while(dy<-Math.PI)dy+=Math.PI*2;
    flightInitialDiff=dy;
    flightFadeout=-1;
    flightLine.visible=true;
    flightMat.opacity=0.8;
    arrowMesh.visible=true;
    arrowMat.opacity=0.95;
    prevPlaneQuat.identity();
    flightGeom.setDrawRange(0,0);
  }

  function updateFlight(){
    if(!flightArcPts){flightLine.visible=false;arrowMesh.visible=false;return;}

    // Fading out phase
    if(flightFadeout>=0){
      flightFadeout+=0.016;
      var fadeT=flightFadeout/0.4;
      var fo=Math.max(0,1-fadeT);
      arrowMat.opacity=fo*0.95;
      planeGlow.material.opacity=fo*0.4;
      if(fadeT>=1){arrowMesh.visible=false;flightLine.visible=false;flightArcPts=null;flightFadeout=-1;}
      return;
    }

    // Only animate during ROTATING state
    if(state!==ROTATING){
      if(flightArcPts)flightFadeout=0;
      return;
    }

    // FIX 2: Calculate progress using signed shortest-path delta
    var dy=tRY-curRY;
    while(dy>Math.PI)dy-=Math.PI*2;
    while(dy<-Math.PI)dy+=Math.PI*2;
    var progress=Math.abs(flightInitialDiff)>0.001?1-dy/flightInitialDiff:1;
    progress=Math.max(0,Math.min(progress,1));

    // Arrowhead runs 1.2x ahead with linear correction
    var arrowProgress=Math.min(Math.pow(progress,0.7)*1.2,1.0);
    var lineProgress=arrowProgress;

    // Update trail line from great circle points
    var drawCount=Math.max(2,Math.round(lineProgress*flightPts)+1);
    if(drawCount>flightPts+1)drawCount=flightPts+1;
    for(var ti=0;ti<drawCount;ti++){
      var idx=Math.min(ti,flightPts);
      var frac=ti/flightPts;
      if(frac>lineProgress){
        var pt=flightArcPts[Math.min(Math.round(lineProgress*flightPts),flightPts)];
        flightPositions[ti*3]=pt.x;flightPositions[ti*3+1]=pt.y;flightPositions[ti*3+2]=pt.z;
      }else{
        var pt=flightArcPts[idx];
        flightPositions[ti*3]=pt.x;flightPositions[ti*3+1]=pt.y;flightPositions[ti*3+2]=pt.z;
      }
    }
    flightGeom.attributes.position.needsUpdate=true;
    flightGeom.setDrawRange(0,drawCount);

    // Position plane along great circle path with smooth orientation
    var aIdx=Math.min(Math.round(arrowProgress*flightPts),flightPts);
    if(aIdx>0&&aIdx<=flightPts){
      arrowMesh.visible=true;
      arrowMesh.position.copy(flightArcPts[aIdx]);
      // Normal = away from globe center (plane faces outward)
      var normal=flightArcPts[aIdx].clone().normalize();
      // Tangent = flight direction
      var prevIdx=Math.max(0,aIdx-1);
      var nextIdx=Math.min(flightPts,aIdx+1);
      var tangent=new THREE.Vector3().subVectors(flightArcPts[nextIdx],flightArcPts[prevIdx]).normalize();
      // Right = perpendicular to both
      var right=new THREE.Vector3().crossVectors(tangent,normal).normalize();
      // Recalculate tangent to be perfectly orthogonal
      tangent.crossVectors(normal,right).normalize();
      // Matrix: X=right, Y=tangent(nose), Z=normal(outward)
      var rotMat=new THREE.Matrix4().makeBasis(right,tangent,normal);
      var targetQuat=new THREE.Quaternion().setFromRotationMatrix(rotMat);
      // Smooth slerp to avoid flicker
      if(prevPlaneQuat.dot(targetQuat)<0)targetQuat.set(-targetQuat.x,-targetQuat.y,-targetQuat.z,-targetQuat.w);
      prevPlaneQuat.slerp(targetQuat,0.12);
      arrowMesh.quaternion.copy(prevPlaneQuat);
    }
  }

  var ROTATING=0,ZOOMING_IN=1,DWELLING=2,ZOOMING_OUT=3;
  var state=ROTATING,tIdx=0,frame=0;
  var DWELL_TIME=450,ZO=3.0,ZI=2.8;
  var clickInitiated=false;
  var curRY=getTargetRotY(locs[0].lng)+0.8,curRX=0,curZ=ZO;
  var tRY=getTargetRotY(locs[0].lng),tRX=getTargetRotX(locs[0].lat);

  // Breadcrumb dots
  var dotsContainer=document.getElementById('globe-dots');
  var dots=dotsContainer?dotsContainer.querySelectorAll('.globe-dot'):[];

  function updateDots(idx){
    dots.forEach(function(d,i){
      d.classList.toggle('active',i===idx);
    });
  }

  dots.forEach(function(d){
    d.addEventListener('click',function(){
      var locIdx=parseInt(d.getAttribute('data-loc'));
      if(locIdx!==tIdx){goToLocation(locIdx);}
    });
  });

  function showCard(loc){
    var step='<span class="card-step">'+(tIdx+1)+' / '+locs.length+'</span>';
    var html='<div class="loc-card" style="--marker-color:rgb('+loc.hex+');--marker-rgb:'+loc.hex+';">'
      +'<div class="card-header"><span class="card-tag">'+loc.tag+'</span>'+step+'</div>'
      +'<div class="card-name">'+loc.name+'</div>'
      +'<div class="card-role">'+loc.proj+'</div>'
      +'<div class="card-divider"></div>'
      +'<div class="card-desc">'+loc.desc+'</div>'
      +'</div>';
    // Decouple DOM swap from render frame to prevent flicker
    cardBox.style.opacity='0';
    requestAnimationFrame(function(){requestAnimationFrame(function(){
      cardBox.innerHTML=html;
      cardBox.style.opacity='1';
    });});
    updateDots(tIdx);
  }
  var hideTimer=null;
  function hideCard(){
    var c=cardBox.querySelectorAll('.loc-card');if(!c.length)return;
    c.forEach(function(el){el.classList.add('hiding');});
    if(hideTimer)clearTimeout(hideTimer);
    hideTimer=setTimeout(function(){cardBox.innerHTML='';hideTimer=null;},250);
  }

  // FIX 2: Shortest path rotation target
  function setShortestTarget(idx){
    tRY=getTargetRotY(locs[idx].lng);
    // Normalize to shortest angular distance from curRY
    var d=tRY-curRY;
    while(d>Math.PI)d-=Math.PI*2;
    while(d<-Math.PI)d+=Math.PI*2;
    tRY=curRY+d;
    tRX=getTargetRotX(locs[idx].lat);
  }

  function goToLocation(idx){
    if(hideTimer){clearTimeout(hideTimer);hideTimer=null;}
    cardBox.innerHTML='';
    var fromIdx=tIdx;
    tIdx=idx;
    setShortestTarget(tIdx);
    state=ROTATING;
    frame=0;
    clickInitiated=true;
    updateDots(tIdx);
    startFlight(fromIdx,tIdx);
  }

  var raycaster=new THREE.Raycaster();
  var mouse=new THREE.Vector2();

  renderer.domElement.addEventListener('click',function(event){
    var rect=renderer.domElement.getBoundingClientRect();
    mouse.x=((event.clientX-rect.left)/rect.width)*2-1;
    mouse.y=-((event.clientY-rect.top)/rect.height)*2+1;
    raycaster.setFromCamera(mouse,camera);
    var intersects=raycaster.intersectObjects(markerMeshes,false);
    if(intersects.length>0){
      goToLocation(intersects[0].object.userData.locIdx);
    }else{
      hideCard();
      var fromClick=tIdx;
      tIdx=(tIdx+1)%locs.length;
      setShortestTarget(tIdx);
      state=ROTATING;
      frame=0;
      updateDots(tIdx);
      startFlight(fromClick,tIdx);
    }
  });

  var t=0;
  function animate(){
    requestAnimationFrame(animate);t+=0.016;frame++;
    // FIX 2: Shortest-path diffY
    var diffY=tRY-curRY;

    var lerpSpeed=clickInitiated?0.025:0.008;
    if(state===ROTATING){
      if(Math.abs(diffY)>0.01){curRY+=diffY*lerpSpeed;curRX+=(tRX-curRX)*lerpSpeed;curZ+=(ZO-curZ)*0.01;}
      else{state=ZOOMING_IN;frame=0;}
    }else if(state===ZOOMING_IN){
      curRY+=(tRY-curRY)*0.04;curZ+=(ZI-curZ)*0.02;curRX+=(tRX-curRX)*0.02;
      if(frame>80){state=DWELLING;frame=0;clickInitiated=false;setTimeout(function(){showCard(locs[tIdx]);},0);}
    }else if(state===DWELLING){
      curRY+=0.00008;
      if(frame>DWELL_TIME){state=ZOOMING_OUT;frame=0;setTimeout(function(){hideCard();},0);}
    }else if(state===ZOOMING_OUT){
      curZ+=(ZO-curZ)*0.02;
      if(frame>60){var fromAuto=tIdx;tIdx=(tIdx+1)%locs.length;setShortestTarget(tIdx);state=ROTATING;frame=0;updateDots(tIdx);startFlight(fromAuto,tIdx);}
    }

    earthGroup.rotation.y=curRY;earthGroup.rotation.x=curRX;camera.position.z=curZ;
    // Smooth marker + ring highlighting - only active during DWELLING
    var SM=0.06;
    for(var mi=0;mi<locs.length;mi++){
      var isActive=(mi===tIdx&&(state===DWELLING||state===ZOOMING_OUT));
      var mDot=markerMeshes[mi];
      var mRing=markerRings[mi];
      // Marker dot opacity - smooth lerp prevents flicker
      var dotTarget=isActive?1.0:0.35;
      mDot.material.opacity+=(dotTarget-mDot.material.opacity)*SM;
      // Ring: smooth pulse for active, smooth dim for inactive
      var rScaleTarget=isActive?1+Math.sin(t*2)*0.2:1;
      var rOpTarget=isActive?0.25+Math.sin(t*2)*0.1:0.08;
      var rs=mRing.scale.x+(rScaleTarget-mRing.scale.x)*SM;
      mRing.scale.set(rs,rs,rs);
      mRing.material.opacity+=(rOpTarget-mRing.material.opacity)*SM;
    }
    updateFlight();
    renderer.render(scene,camera);
  }
  animate();

  var resizeTimer;
  window.addEventListener('resize',function(){
    clearTimeout(resizeTimer);
    resizeTimer=setTimeout(function(){
      var r=gw.getBoundingClientRect();var ns=Math.round(r.width);
      renderer.setSize(ns,ns);renderer.setPixelRatio(window.devicePixelRatio);
      camera.updateProjectionMatrix();
    },150);
  });
}
