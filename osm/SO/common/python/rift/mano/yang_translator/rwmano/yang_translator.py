# Copyright 2016 RIFT.io Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import shutil
import subprocess
import tarfile

from rift.mano.yang_translator.common.exception import ValidationError
from rift.mano.yang_translator.common.utils import _
from rift.mano.yang_translator.rwmano.syntax.tosca_resource \
    import ToscaResource
from rift.mano.yang_translator.rwmano.syntax.tosca_template \
    import ToscaTemplate
from rift.mano.yang_translator.rwmano.translate_descriptors \
    import TranslateDescriptors

import rift.package.image
from rift.package.package import TarPackageArchive
import rift.package.cloud_init
import rift.package.script
import rift.package.store
import rift.package.icon

class YangTranslator(object):
    '''Invokes translation methods.'''

    def __init__(self, log, yangs=None, files=None, packages=[]):
        super(YangTranslator, self).__init__()
        self.log = log
        self.yangs = {}
        if yangs is not None:
            self.yangs = yangs
        self.files = files
        self.archive = None
        self.tosca_template = ToscaTemplate(log)
        self.node_translator = None
        self.pkgs = packages
        self.output_files = {}
        self.output_files['nsd'] = []
        self.output_files['vnfd'] = []

        log.info(_('Initialized parameters for translation.'))

    def translate(self):
        if self.files:
            self.get_yangs()
        else:
            if 'nsd' in self.yangs:
                self.output_files['nsd'].append(self.yangs['nsd'][0]['short_name'].replace(' ','_'))
            if 'vnfd' in self.yangs:
                for yang_vnfd in self.yangs['vnfd']:
                    self.output_files['vnfd'].append(yang_vnfd['short_name'].replace(' ','_'))

        self.node_translator = TranslateDescriptors(self.log,
                                                      self.yangs,
                                                      self.tosca_template,
                                                      self.output_files['vnfd'])
        self.tosca_template.resources = self.node_translator.translate()


        return self.tosca_template.output_to_tosca()

    def get_yangs(self):
        '''Get the descriptors and convert to yang instances'''
        for filename in self.files:
            self.log.debug(_("Load file {0}").format(filename))

            # Only one descriptor per file
            if tarfile.is_tarfile(filename):
                tar = open(filename, "r+b")
                archive = TarPackageArchive(self.log, tar)
                pkg = archive.create_package()
                self.pkgs.append(pkg)
                desc_type = pkg.descriptor_type
                if desc_type == TranslateDescriptors.NSD:
                    if TranslateDescriptors.NSD not in self.yangs:
                        self.yangs[TranslateDescriptors.NSD] = []
                    self.yangs[TranslateDescriptors.NSD]. \
                        append(pkg.descriptor_msg.as_dict())
                    if 'name' in pkg.descriptor_msg.as_dict() is not None:
                        self.output_files['nsd'].append(pkg.descriptor_msg.as_dict()['name'])
                    else:
                        raise ValidationError(message="NSD Descriptor name attribute is not populated ")
                elif desc_type == TranslateDescriptors.VNFD:
                    if TranslateDescriptors.VNFD not in self.yangs:
                        self.yangs[TranslateDescriptors.VNFD] = []
                    self.yangs[TranslateDescriptors.VNFD]. \
                        append(pkg.descriptor_msg.as_dict())
                    if 'name' in pkg.descriptor_msg.as_dict() is not None:
                        self.output_files['vnfd'].append(pkg.descriptor_msg.as_dict()['name'])
                    else:
                        raise ValidationError(message="VNFD Descriptor name attribute is not populated ")
                else:
                    raise ValidationError("Unknown descriptor type: {}".
                                          format(desc_type))

    def _create_csar_files(self, output_dir, tmpl_out,
                           archive=False):
        '''
        for tmpl in tmpl_out:
            if ToscaTemplate.TOSCA not in tmpl:
                self.log.error(_("Did not find TOSCA template for {0}").
                           format(tmpl))
                return
        '''
        # Create sub for each NS template
        sub_folder_name = None
        if self.files:
            if len(self.output_files['nsd']) > 0:
                if len(self.output_files['nsd']) == 1:
                    sub_folder_name = self.output_files['nsd'][0]
                else:
                    raise ValidationError(message="Multiple NSD Descriptor uploaded ")
            elif len(self.output_files['vnfd']) > 0:
                if len(self.output_files['vnfd']) == 1:
                    sub_folder_name = self.output_files['vnfd'][0]
                else:
                    raise ValidationError(message="Multiple VNFDs Descriptors uploaded without NSD")
            else:
                raise ValidationError(message="No NSD or VNFD uploaded")
        else:
            if 'nsd' in self.yangs:
                sub_folder_name = self.yangs['nsd'][0]['short_name'].replace(' ','_')
            elif 'vnfd' in self.yangs:
                sub_folder_name = self.yangs['vnfd'][0]['short_name'].replace(' ','_')


        subdir = os.path.join(output_dir, sub_folder_name)
        if os.path.exists(subdir):
            shutil.rmtree(subdir)
        os.makedirs(subdir)
        riftio_src_file = "{0}{1}".format(os.getenv('RIFT_INSTALL'), "/usr/rift/mano/common/riftiotypes.yaml")
        # Create the definitions dir
        def_dir = os.path.join(subdir, 'Definitions')
        os.makedirs(def_dir)
        shutil.copy2(riftio_src_file, def_dir + "/riftiotypes.yaml")
        tosca_meta_entry_file = None
        for tmpl_key in tmpl_out:
            tmpl = tmpl_out[tmpl_key]
            file_name = tmpl_key.replace(' ','_')
            entry_file = os.path.join(def_dir, file_name+'.yaml')
            if file_name.endswith('nsd'):
                tosca_meta_entry_file = file_name
            self.log.debug(_("Writing file {0}").
                           format(entry_file))
            with open(entry_file, 'w+') as f:
                f.write(tmpl[ToscaTemplate.TOSCA])

        if tosca_meta_entry_file is None:
            tosca_meta_entry_file = sub_folder_name
        # Create the Tosca meta
        meta_dir = os.path.join(subdir, 'TOSCA-Metadata')
        os.makedirs(meta_dir)
        meta = '''TOSCA-Meta-File-Version: 1.0
CSAR-Version: 1.1
Created-By: RIFT.io
Entry-Definitions: Definitions/'''
        meta_data = "{}{}".format(meta, tosca_meta_entry_file+'.yaml')
        meta_file = os.path.join(meta_dir, 'TOSCA.meta')
        self.log.debug(_("Writing file {0}:\n{1}").
                       format(meta_file, meta_data))
        with open(meta_file, 'w+') as f:
            f.write(meta_data)

        # Copy other supporting files
        for key in tmpl_out:
            tmpl = tmpl_out[key]
            if ToscaTemplate.FILES in tmpl:
                for f in tmpl[ToscaTemplate.FILES]:
                    self.log.debug(_("Copy supporting file {0}").format(f))

                    # Search in source packages
                    if len(self.pkgs):
                        for pkg in self.pkgs:
                            # TODO(pjoseph): Need to add support for other file types
                            fname = f[ToscaResource.NAME]
                            dest_path = os.path.join(subdir, f[ToscaResource.DEST])
                            ftype = f[ToscaResource.TYPE]

                            if ftype == 'image':
                                image_file_map = rift.package.image.get_package_image_files(pkg)

                                if fname in image_file_map:
                                    self.log.debug(_("Extracting image {0} to {1}").
                                                   format(fname, dest_path))
                                    pkg.extract_file(image_file_map[fname],
                                                     dest_path)
                                    break

                            elif ftype == 'script':
                                script_file_map = \
                                    rift.package.script.PackageScriptExtractor.package_script_files(pkg)
                                if fname in script_file_map:
                                    self.log.debug(_("Extracting script {0} to {1}").
                                                   format(fname, dest_path))
                                    pkg.extract_file(script_file_map[fname],
                                                     dest_path)
                                    break

                            elif ftype == 'cloud_init':
                                script_file_map = \
                                    rift.package.cloud_init.PackageCloudInitExtractor.package_script_files(pkg)
                                if fname in script_file_map:
                                    self.log.debug(_("Extracting script {0} to {1}").
                                                   format(fname, dest_path))
                                    pkg.extract_file(script_file_map[fname],
                                                     dest_path)
                                    break
                            elif ftype == 'icons':
                                icon_file_map = \
                                    rift.package.icon.PackageIconExtractor.package_icon_files(pkg)
                                if fname in icon_file_map:
                                    self.log.debug(_("Extracting script {0} to {1}").
                                                   format(fname, dest_path))
                                    pkg.extract_file(icon_file_map[fname],
                                                     dest_path)
                                    break

                            else:
                                self.log.warn(_("Unknown file type {0}: {1}").
                                              format(ftype, f))

                    #TODO(pjoseph): Search in other locations

        # Create the ZIP archive
        if archive:
            prev_dir=os.getcwd()
            os.chdir(subdir)

            try:
                zip_file = sub_folder_name + '.zip'
                zip_path = os.path.join(output_dir, zip_file)
                self.log.debug(_("Creating zip file {0}").format(zip_path))
                zip_cmd = "zip -r {}.partial ."
                subprocess.check_call(zip_cmd.format(zip_path),
                                      shell=True,
                                      stdout=subprocess.DEVNULL)
                mv_cmd = "mv {0}.partial {0}"
                subprocess.check_call(mv_cmd.format(zip_path),
                                      shell=True,
                                      stdout=subprocess.DEVNULL)
                shutil.rmtree(subdir)
                return zip_path

            except subprocess.CalledProcessError as e:
                self.log.error(_("Creating CSAR archive failed: {0}").
                               format(e))

            except Exception as e:
                self.log.exception(e)

            finally:
                os.chdir(prev_dir)

    def write_output(self, output,
                     output_dir=None,
                     archive=False,):
        if output:
            zip_files = []
            #for key in output.keys():
            if output_dir:
                zf = self._create_csar_files(output_dir,
                                             output,
                                             archive=archive,)
                zip_files.append(zf)
            else:
                print(_("There is an issue with TOSCA Template"))
            return zip_files
