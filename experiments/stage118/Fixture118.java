package org.ffbe.diagnostic95;
import android.content.Context;
import android.system.Os;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
/** Fresh private fixture only. No intent paths, external storage or real profile. */
final class Fixture118 {
 static final String PREFIX="startup118/";
 static final String[] TARGETS={"state/campaign.json","state/slots/index.json","prefs/gamedata.xml","data/registry.json"};
 static final String[] NAMES={"original","catalogue","prefs","registry"};
 private static File engine;
 final File root;private final byte[] proposal;final String binding,expected;
 private Fixture118(File root,byte[] p,String b)throws Exception{this.root=root;proposal=p.clone();binding=b;expected=Disk95.digest(p);}
 byte[] proposal(){return proposal.clone();}
 static byte[] asset(Context c,String name)throws Exception {
  String[] pin=null;for(String[] e:AssetPins118.ALL)if(e[0].equals(name))pin=e;
  Disk95.require(pin!=null);int len=Integer.parseInt(pin[1]);
  try(InputStream in=c.getAssets().open(PREFIX+name);ByteArrayOutputStream out=new ByteArrayOutputStream(len)){
   byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){Disk95.require(out.size()+n<=len);out.write(b,0,n);}byte[] raw=out.toByteArray();Disk95.require(raw.length==len&&Disk95.digest(raw).equals(pin[2]));return raw;
  }
 }
 static File fresh(Context c,String prefix)throws Exception{File b=c.getFilesDir().getCanonicalFile(),f=new File(b,prefix+UUID.randomUUID().toString().replace("-",""));Disk95.require(f.getCanonicalFile().equals(f.getAbsoluteFile()));Os.mkdir(f.getPath(),0700);return f;}
 static void dir(File root,String n)throws Exception{Os.mkdir(new File(root,n).getPath(),0700);}
 static void put(File root,String n,byte[] b)throws Exception{File f=new File(root,n);Disk95.exclusive(f,b);Os.chmod(f.getPath(),0600);Disk95.require(Arrays.equals(Disk95.read(f),b));}
 static synchronized void engine(Context c)throws Exception{
  if(engine!=null)return;
  if(Python.isStarted())throw new IOException("Unexpected Python initialization");
  File e=fresh(c,"engine118-");dir(e,"mst_decoded");
  for(String[] pin:AssetPins118.ALL)if(pin[0].startsWith("engine/"))put(e,pin[0].substring(7),asset(c,pin[0]));
  Python.start(new AndroidPlatform(c));
  try(PyObject mod=Python.getInstance().getModule("boot118");PyObject result=mod.callAttr("configure",e.getPath())){Disk95.require("FIXTURE_ENGINE_READY".equals(result.toString()));}
  engine=e;
 }
 static Fixture118 prepare(Context c)throws Exception{
  byte[] original=asset(c,"fixture/original"),p=asset(c,"fixture/proposal");StartupReview114.verify(original,p);
  File root=fresh(c,"ffbe117-fixture-");for(String n:new String[]{"state","state/slots","prefs","files","data","profile-backup","transaction-backup","staging"})dir(root,n);
  for(int i=0;i<TARGETS.length;i++)put(root,TARGETS[i],asset(c,"fixture/"+NAMES[i]));put(root,"writer.lock",new byte[0]);
  String b=Disk95.digest(("FFBE-STARTUP-FIXTURE-114\n"+Disk95.digest(original)+"\n"+Disk95.digest(asset(c,"fixture/catalogue"))+"\n"+Disk95.digest(asset(c,"fixture/registry"))+"\n"+Disk95.digest(asset(c,"fixture/prefs"))+"\n"+Disk95.digest(p)).getBytes(StandardCharsets.UTF_8));
  Disk95.require(b.equals(new String(asset(c,"fixture/binding"),StandardCharsets.US_ASCII)));return new Fixture118(root,p,b);
 }
}
